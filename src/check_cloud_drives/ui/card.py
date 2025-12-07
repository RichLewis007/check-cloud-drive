"""Drive card UI component."""

import re
from datetime import datetime

from PySide6.QtCore import Property, QEasingCurve, QMimeData, QPoint, QPropertyAnimation, Qt, QRect, QSize, QTimer, Signal
from PySide6.QtGui import QColor, QDrag, QFontMetrics, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models import DriveConfig, DriveStatus
from .utils import load_icon


def format_relative_time(timestamp_str: str) -> str:
    """Format a timestamp string as relative time (e.g., '10 minutes ago').

    Handles formats like '2024-01-15 14:30:00' and returns relative time.
    Does not report seconds. Handles edge cases like 'Never' gracefully.
    """
    try:
        # Handle special cases
        if not timestamp_str or timestamp_str.lower() in ["never", "unknown", ""]:
            return timestamp_str

        # Parse the timestamp
        timestamp = None
        if isinstance(timestamp_str, str):
            # Try common datetime formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%H:%M:%S"]:
                try:
                    timestamp = datetime.strptime(timestamp_str, fmt)
                    # If only time was provided (HH:MM:SS), assume today
                    if fmt == "%H:%M:%S":
                        now = datetime.now()
                        timestamp = timestamp.replace(year=now.year, month=now.month, day=now.day)
                    break
                except ValueError:
                    continue

        if timestamp is None:
            return timestamp_str  # Return as-is if can't parse

        # Calculate difference
        now = datetime.now()
        diff = now - timestamp

        total_seconds = int(diff.total_seconds())

        # If negative (future time), return as-is
        if total_seconds < 0:
            return timestamp_str

        # Calculate components
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        # Build relative time string
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0 or len(parts) == 0:  # Always show minutes if no days/hours
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

        if len(parts) == 0:
            return "just now"

        return ", ".join(parts) + " ago"
    except Exception:
        return timestamp_str  # Return as-is on error


class LoadingSpinner(QWidget):
    """Custom widget that draws an animated rotating spinner."""

    def __init__(self, parent=None, size=32, color="#f39c12"):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setMinimumSize(size, size)
        self.color = QColor(color)
        self._angle = 0  # Private attribute to store the angle

        # Animation
        self.animation = QPropertyAnimation(self, b"angle")
        self.animation.setDuration(1000)  # 1 second per rotation
        self.animation.setStartValue(360)  # Start at 360
        self.animation.setEndValue(0)  # End at 0 (counter-clockwise)
        self.animation.setLoopCount(-1)  # Infinite loop
        self.animation.setEasingCurve(QEasingCurve.Linear)

    def get_angle(self):
        return self._angle

    def set_angle(self, value):
        self._angle = value
        self.update()  # Trigger repaint

    angle = Property(int, get_angle, set_angle)

    def paintEvent(self, event):
        """Draw the rotating spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate radius
        radius = min(self.width(), self.height()) // 2 - 4
        pen_width = max(3, radius // 6)

        # Set up pen
        pen = QPen(self.color)
        pen.setWidth(pen_width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        # Draw arc that rotates
        # Start angle: current rotation angle
        # Span angle: 270 degrees (3/4 of a circle for a nice effect)
        start_angle = (self._angle - 90) * 16  # Qt uses 1/16th of a degree units
        span_angle = 270 * 16

        # Draw the arc
        rect = self.rect().adjusted(pen_width, pen_width, -pen_width, -pen_width)
        painter.drawArc(rect, start_angle, span_angle)

    def start(self):
        """Start the spinner animation."""
        self.animation.start()
        self.show()

    def stop(self):
        """Stop the spinner animation."""
        self.animation.stop()
        self.hide()


class DriveCard(QFrame):
    """Widget representing a single cloud drive card."""
    
    # Signal emitted when display name is saved
    display_name_saved = Signal(str)  # Emits the new display name
    # Signal emitted when card should be removed
    card_removed = Signal()  # Emits when card should be removed

    def __init__(self, drive_config: DriveConfig, parent=None):
        super().__init__(parent)
        self.drive_config = drive_config
        self.drive_status: DriveStatus | None = None
        self.is_updating = False
        self.is_edit_mode = False
        self.drag_start_position = QPoint()
        self.setAcceptDrops(True)  # Enable drop events
        self.last_updated_str: str | None = None  # Store last updated timestamp string
        # Timer to update relative time every minute
        self.time_update_timer = QTimer(self)
        self.time_update_timer.timeout.connect(self._update_relative_time)
        self.time_update_timer.start(60000)  # Update every 60 seconds (1 minute)
        self._setup_ui()
        # Store the initial minimum height to maintain card size in edit mode
        self._initial_min_height = self.minimumHeight()
        # Store original stylesheet for drag/drop restoration
        self._original_stylesheet = self.styleSheet()
        # Store height for drag over effect
        self._drag_over_height = None
        # Store original content for drag preview restoration
        self._original_content_state = None
        self._preview_target_card = None  # Card showing preview content

    def _setup_ui(self):
        """Set up the UI for the drive card."""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 4px 6px;
                margin: 4px;
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
            QFrame:hover {
                border-color: #4a90e2;
                background-color: #f8f9fa;
            }
            QFrame[dragging="true"] {
                opacity: 0.5;
            }
            QLineEdit {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px;
                color: #2c3e50;
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
                background-color: #ffffff;
            }
            QLabel {
                color: #2c3e50;
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
        """)

        # Set maximum width for the card to prevent it from becoming too wide
        self.setMaximumWidth(400)  # Reasonable maximum width for cards
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove default layout margins
        layout.setSpacing(4)

        # Header with icon on left and title next to it
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)  # Remove default layout margins
        
        # Icon (will load SVG if available, otherwise placeholder)
        # Icon stays visible in both normal and edit mode
        icon_label = QLabel()
        icon_base_size = 52  # Base size for visibility without being too large
        icon_pixmap, aspect_ratio = load_icon(self.drive_config.drive_type, size=icon_base_size)
        
        # Calculate dimensions based on aspect ratio
        # The load_icon function already returns a pixmap with correct aspect ratio
        # We just need to match the label size to the pixmap size
        icon_width = icon_pixmap.width()
        icon_height = icon_pixmap.height()
        
        # Limit icon width to prevent cards from becoming too wide
        # Maximum icon width should be reasonable (e.g., 70px for wide icons)
        max_icon_width = 70
        if icon_width > max_icon_width:
            # Scale down proportionally
            scale_factor = max_icon_width / icon_width
            icon_width = max_icon_width
            icon_height = int(icon_height * scale_factor)
            # Scale the pixmap to match
            icon_pixmap = icon_pixmap.scaled(
                icon_width, icon_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        
        icon_label.setFixedSize(icon_width, icon_height)
        icon_label.setMinimumSize(icon_width, icon_height)
        icon_label.setAlignment(Qt.AlignCenter)
        # Don't use setScaledContents - the pixmap is already the correct size
        # This prevents distortion
        icon_label.setScaledContents(False)
        # Remove any default styling that might create borders or backgrounds
        icon_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap)
        self.icon_label = icon_label

        # Icon on the left (always visible) - align to top
        header_layout.addWidget(icon_label, 0, Qt.AlignTop)
        
        # Name and remote name labels - next to icon (hidden in edit mode)
        name_layout = QVBoxLayout()
        name_layout.setContentsMargins(0, 0, 0, 0)  # Remove default layout margins
        name_layout.setSpacing(8)  # Increased spacing to accommodate 2-line title and move Remote line down
        # Display name as non-editable title label (can wrap to 2 lines, then truncate)
        self.display_name_label = QLabel(self.drive_config.display_name)
        self.display_name_label.setStyleSheet("""
            QLabel {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
                border: none;
                padding: 2px 0px;
            }
        """)
        self.display_name_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.display_name_label.setWordWrap(True)
        # Set maximum height for 2 lines
        font = self.display_name_label.font()
        font.setPointSize(16)
        font.setBold(True)
        font.setFamily("AtkynsonMono Nerd Font Propo")
        self.display_name_label.setFont(font)
        metrics = QFontMetrics(font)
        single_line_height = metrics.height()  # Actual line height
        line_spacing = metrics.lineSpacing()  # Line spacing (includes leading)
        # For 2 lines: use lineSpacing * 2 which gives us enough space for 2 full lines
        # lineSpacing already includes the line height plus leading, so * 2 gives us 2 lines
        two_line_height = int(line_spacing * 2.0)  # Generous space for 2 lines
        # Store max_height for truncation logic
        self._title_max_height = two_line_height
        
        # CRITICAL: QLabel word wrap requires a fixed or maximum width to work
        # Calculate available width: card max (400) - icon (70) - padding (30) = ~300px
        # We'll update this dynamically after layout, but set an initial value
        initial_width = 300
        self.display_name_label.setMaximumWidth(initial_width)
        
        # Set size policy: Fixed/Preferred horizontally (width constrained), 
        # MinimumExpanding vertically (can grow to show 2 lines)
        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        policy.setHeightForWidth(False)  # Don't adjust height based on width
        self.display_name_label.setSizePolicy(policy)
        
        # Set minimum height for 1 line, maximum for 2 lines
        self.display_name_label.setMinimumHeight(single_line_height)
        self.display_name_label.setMaximumHeight(two_line_height)
        
        name_layout.addWidget(self.display_name_label, 1)  # Add stretch factor so it expands
        
        # Set initial display name (will be updated on resize if needed)
        # Use a timer to update after layout is complete
        QTimer.singleShot(100, lambda: self.update_display_name(self.drive_config.display_name))
        # Force the label to update its geometry after being added to layout
        # This ensures word wrap has the correct width to work with
        QTimer.singleShot(150, lambda: self._update_label_width())

        # Remote name will be added at the bottom of the card later
        # Create it now but don't add to name_layout
        self.remote_name_label = QLabel(f"Remote: {self.drive_config.remote_name}")
        self.remote_name_label.setStyleSheet("""
            QLabel {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 11px;
                color: #7f8c8d;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
        """)
        self.remote_name_label.setAlignment(Qt.AlignLeft)
        
        # Wrap name_layout in a widget container for easier show/hide
        name_container = QWidget()
        name_container.setLayout(name_layout)
        self.name_container = name_container
        
        # Add name container to header, with stretch to take remaining space
        header_layout.addWidget(name_container, 1)
        header_layout.addStretch()  # Push everything to the left
        
        # Store header_layout reference for edit mode swapping
        self.header_layout = header_layout
        self.name_layout = name_layout
        
        # Wrap header_layout in a widget for easier show/hide
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        self.header_layout_widget = header_widget
        layout.addWidget(header_widget)

        # Status information
        self.status_label = QLabel("Status: Not updated")
        self.status_label.setStyleSheet(
            "color: #7f8c8d; font-size: 13px; font-family: 'AtkynsonMono Nerd Font Propo', monospace;"
        )
        layout.addWidget(self.status_label)

        # Drive info
        self.info_label = QLabel("Click 'Refresh All' to update")
        self.info_label.setStyleSheet(
            "color: #5a6c7d; font-size: 11px; font-family: 'AtkynsonMono Nerd Font Propo', monospace;"
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Bottom section with update indicator, free space, and settings icon
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)  # Remove default layout margins

        # Update indicator at bottom left (shows animated spinner when updating)
        # Use a spacer widget to reserve space even when hidden, so free space stays centered
        update_spacer = QWidget()
        update_spacer.setFixedSize(32, 32)
        self.update_indicator = LoadingSpinner(self, size=32, color="#f39c12")
        self.update_indicator.setToolTip(
            "Update status indicator - shows when drive is being refreshed"
        )
        self.update_indicator.hide()  # Hidden by default
        bottom_layout.addWidget(update_spacer)  # Reserve space for update indicator

        # Free space label at bottom center (bold, red, title size)
        self.free_space_label = QLabel("")
        self.free_space_label.setStyleSheet("""
            QLabel {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 16px;
                font-weight: bold;
                color: #e74c3c;
                background-color: transparent;
                border: none;
                padding: 6px 0px 2px 0px;
            }
        """)
        self.free_space_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.free_space_label.hide()  # Hidden until status is updated
        bottom_layout.addStretch()  # Stretch before free space
        bottom_layout.addWidget(self.free_space_label, 0, Qt.AlignCenter | Qt.AlignVCenter)
        bottom_layout.addStretch()  # Stretch after free space

        # Settings icon (Nerd Font) at bottom right - make it a button for clickability
        settings_button = QPushButton("\uf013")  # nf-fa-cog (gear icon)
        settings_button.setStyleSheet("""
            QPushButton {
                color: #5a6c7d;
                font-size: 24px;
                font-family: 'AtkynsonMono Nerd Font Propo', monospace;
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                color: #4a90e2;
            }
        """)
        settings_button.setToolTip("Edit card title")
        settings_button.setFixedSize(32, 32)  # Match update indicator size
        settings_button.setMinimumSize(32, 32)
        settings_button.clicked.connect(self._enter_edit_mode)
        self.settings_button = settings_button
        bottom_layout.addWidget(settings_button)
        
        # Store reference to update_spacer so we can show/hide the indicator on it
        self.update_spacer = update_spacer

        layout.addLayout(bottom_layout)
        
        # Remote name at the very bottom of the card
        layout.addWidget(self.remote_name_label)
        
        # Store references to widgets that need to be hidden in edit mode
        # Note: icon_label stays visible in edit mode
        self.normal_mode_widgets = [
            self.display_name_label,
            self.remote_name_label,
            self.status_label,
            self.info_label,
            self.free_space_label,
            self.update_spacer,
            self.update_indicator,
            settings_button,
        ]
        
        # Create edit mode UI (initially hidden)
        self._create_edit_mode_ui(layout)
    
    def _create_edit_mode_ui(self, main_layout):
        """Create the edit mode UI elements."""
        # Edit mode container (initially hidden)
        # This will be added to main layout when in edit mode
        self.edit_mode_container = QWidget()
        edit_layout = QVBoxLayout(self.edit_mode_container)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        edit_layout.setSpacing(8)
        
        # Title edit field (3 lines, fills card width)
        # Icon is already visible in header_layout above at top left
        self.title_edit = QTextEdit()
        self.title_edit.setPlainText(self.drive_config.display_name)
        self.title_edit.setStyleSheet("""
            QTextEdit {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px;
            }
            QTextEdit:focus {
                border-color: #4a90e2;
                background-color: #ffffff;
            }
        """)
        # Set height for exactly 3 lines
        # Set the font first
        font = self.title_edit.font()
        font.setPointSize(16)
        font.setBold(True)
        font.setFamily("AtkynsonMono Nerd Font Propo")
        self.title_edit.setFont(font)
        
        # Remove document margins to get accurate line height
        self.title_edit.document().setDocumentMargin(0)
        
        # Use QFontMetrics to get exact line height
        metrics = QFontMetrics(font)
        # height() gives the height of a single line of text
        # lineSpacing() gives the recommended line spacing (height + leading)
        # For 3 lines, we want: first line + 2 * line spacing
        single_line_height = metrics.height()
        line_spacing = metrics.lineSpacing()
        # Total for 3 lines: first line + 2 * line spacing
        total_height = single_line_height + (line_spacing * 2)
        # Add padding (4px top + 4px bottom = 8px)
        height_with_padding = total_height + 8
        self.title_edit.setFixedHeight(int(height_with_padding))
        self.title_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Limit to 3 lines by setting maximum block count
        self.title_edit.document().setMaximumBlockCount(3)
        edit_layout.addWidget(self.title_edit, 1)  # Stretch factor 1 to fill available space
        
        # Buttons at bottom, centered
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Create a reference button to get standard height (matching dialog buttons)
        from PySide6.QtWidgets import QPushButton as RefButton
        ref_button = RefButton("Cancel")
        ref_button.setStyleSheet("""
            QPushButton {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 12px;
            }
        """)
        standard_button_height = ref_button.sizeHint().height()
        ref_button.deleteLater()
        
        # Cancel button (to the left of Save)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedHeight(standard_button_height)
        cancel_button.setStyleSheet("""
            QPushButton {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:pressed {
                background-color: #bfc9ca;
            }
        """)
        cancel_button.clicked.connect(self._cancel_edit)
        buttons_layout.addWidget(cancel_button)
        
        # Save button (green) - same height as Cancel
        save_button = QPushButton("Save")
        save_button.setFixedHeight(standard_button_height)
        save_button.setStyleSheet("""
            QPushButton {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                font-weight: bold;
                color: #ffffff;
                background-color: #27ae60;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        save_button.clicked.connect(self._save_edit)
        buttons_layout.addWidget(save_button)
        
        buttons_layout.addStretch()
        edit_layout.addLayout(buttons_layout)
        
        # Remove Remote button (red, below Save/Cancel)
        remove_button_layout = QHBoxLayout()
        remove_button_layout.addStretch()
        
        remove_button = QPushButton("Remove Remote")
        # Match Save/Cancel button height, but allow width to fit text
        remove_button.setFixedHeight(standard_button_height)
        remove_button.setStyleSheet("""
            QPushButton {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                font-weight: bold;
                color: #ffffff;
                background-color: #e74c3c;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        remove_button.clicked.connect(self._remove_card)
        remove_button_layout.addWidget(remove_button)
        
        remove_button_layout.addStretch()
        edit_layout.addLayout(remove_button_layout)
        
        # Edit mode container is not added to layout yet
        # It will be inserted into header_layout when entering edit mode
        self.edit_mode_container.hide()
    
    def _enter_edit_mode(self):
        """Enter edit mode - hide normal widgets, show edit widgets."""
        if self.is_edit_mode:
            return
        
        self.is_edit_mode = True
        
        # Store current height and set fixed height to prevent resizing
        current_height = self.sizeHint().height()
        if current_height <= 0:
            current_height = self.height()
        if current_height > 0:
            self.setFixedHeight(current_height)
        
        # Hide name labels (icon stays visible)
        self.display_name_label.hide()
        self.remote_name_label.hide()
        
        # Hide other normal mode widgets (status, info, bottom section)
        for widget in self.normal_mode_widgets:
            if widget not in [self.display_name_label, self.remote_name_label]:
                widget.hide()
        
        # Hide name container (icon stays visible in header_layout)
        self.name_container.hide()
        # Add edit_mode_container to main layout (after header_layout which contains icon)
        # Find header_layout_widget position in main layout
        main_layout = self.layout()
        header_index = -1
        for i in range(main_layout.count()):
            item = main_layout.itemAt(i)
            if item and item.widget() == self.header_layout_widget:
                header_index = i
                break
        
        if header_index >= 0:
            # Insert edit_mode_container right after header_layout_widget
            main_layout.insertWidget(header_index + 1, self.edit_mode_container, 1)
        else:
            # Fallback: add at the beginning
            main_layout.insertWidget(0, self.edit_mode_container, 1)
        self.edit_mode_container.show()
        
        # Set the title edit text
        self.title_edit.setPlainText(self.drive_config.display_name)
        self.title_edit.setFocus()
        self.title_edit.selectAll()
    
    def _exit_edit_mode(self):
        """Exit edit mode - show normal widgets, hide edit widgets."""
        if not self.is_edit_mode:
            return
        
        self.is_edit_mode = False
        
        # Restore height constraints - allow card to resize naturally
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX equivalent
        
        # Hide edit container and show header_layout_widget again
        main_layout = self.layout()
        edit_container_index = -1
        for i in range(main_layout.count()):
            item = main_layout.itemAt(i)
            if item and item.widget() == self.edit_mode_container:
                edit_container_index = i
                break
        
        if edit_container_index >= 0:
            # Remove edit_mode_container from main layout
            main_layout.removeWidget(self.edit_mode_container)
            self.edit_mode_container.hide()
        
        # Show header_layout_widget again (icon stays visible)
        if hasattr(self, 'header_layout_widget') and self.header_layout_widget:
            self.header_layout_widget.show()
        
        # Show name container (it's still in the layout, just was hidden)
        self.name_container.show()
        
        # Show name labels
        self.display_name_label.show()
        self.remote_name_label.show()
        
        # Show all other normal mode widgets
        for widget in self.normal_mode_widgets:
            if widget not in [self.display_name_label, self.remote_name_label]:
                widget.setVisible(True)
    
    def _save_edit(self):
        """Save the edited title."""
        new_title = self.title_edit.toPlainText().strip()
        if not new_title:
            # Don't allow empty titles
            return
        
        # Update the drive config
        self.drive_config.display_name = new_title
        
        # Update the display label (will be truncated if needed)
        self.update_display_name(new_title)
        
        # Emit signal to notify parent to save config
        self.display_name_saved.emit(new_title)
        
        # Exit edit mode
        self._exit_edit_mode()
    
    def _remove_card(self):
        """Remove the card from the list."""
        # Emit signal to remove the card
        self.card_removed.emit()
        # Exit edit mode (card will be removed by parent)
        self._exit_edit_mode()
    
    def _cancel_edit(self):
        """Cancel editing and exit edit mode."""
        # Restore original text
        self.title_edit.setPlainText(self.drive_config.display_name)
        
        # Exit edit mode
        self._exit_edit_mode()

    def _update_label_width(self):
        """Update the label's maximum width based on available space and force word wrap."""
        if hasattr(self, 'display_name_label') and hasattr(self, 'icon_label'):
            # Get actual card width
            card_width = self.width() if self.width() > 0 else 400
            icon_width = self.icon_label.width() if hasattr(self, 'icon_label') else 70
            # Calculate available width: card width - icon - padding/margins
            available_width = card_width - icon_width - 30  # Padding and margins
            if available_width > 0:
                # Set maximum width - this is CRITICAL for word wrap to work
                self.display_name_label.setMaximumWidth(available_width)
                # Force a text update to trigger word wrap recalculation with new width
                current_text = self.display_name_label.text()
                if current_text:
                    # Re-set the text to force word wrap recalculation
                    self.display_name_label.setText("")  # Clear first
                    QTimer.singleShot(10, lambda: self.display_name_label.setText(current_text))
    
    def update_display_name(self, name: str):
        """Update the display name label with truncation for 2 lines."""
        self.drive_config.display_name = name
        # Truncate text if it exceeds 2 lines
        font = self.display_name_label.font()
        metrics = QFontMetrics(font)
        # Use the stored max height from initialization
        max_height = getattr(self, '_title_max_height', None)
        if max_height is None:
            # Fallback calculation if not set
            line_spacing = metrics.lineSpacing()
            max_height = int(line_spacing * 2.0)
        
        # Get available width (card width minus icon and padding)
        # Use a reasonable estimate if card width not yet set
        card_width = self.width() if self.width() > 0 else 400
        icon_width = self.icon_label.width() if hasattr(self, 'icon_label') else 70
        available_width = card_width - icon_width - 30  # Padding and margins
        if available_width <= 0:
            available_width = 300  # Fallback width
        
        # Try to manually split text into 2 lines for better control
        # Split on words and try to create 2 balanced lines
        words = name.split()
        if len(words) > 1 and len(name) > 20:
            # Try to split into 2 lines
            mid_point = len(words) // 2
            line1 = " ".join(words[:mid_point])
            line2 = " ".join(words[mid_point:])
            
            # Check if this fits in 2 lines (without word wrap flag for manual line breaks)
            test_text = f"{line1}\n{line2}"
            test_rect = metrics.boundingRect(QRect(0, 0, available_width, 10000),
                                            Qt.AlignLeft | Qt.AlignTop, test_text)
            
            if test_rect.height() <= max_height:
                # It fits, use the 2-line version with explicit line break
                self.display_name_label.setText(test_text)
                self.display_name_label.setToolTip(name)  # Show full text on hover
                return
        
        # If manual split doesn't work or text is too short, use word wrap
        # Calculate how many lines the text would take with word wrapping
        text_rect = metrics.boundingRect(QRect(0, 0, available_width, 10000), 
                                         Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, name)
        
        # Only truncate if text exceeds 2 lines (max_height)
        if text_rect.height() > max_height:
            # Text exceeds 2 lines, need to truncate
            # Binary search for the right length
            low = 0
            high = len(name)
            best_text = name
            
            while low < high:
                mid = (low + high + 1) // 2
                test_text = name[:mid] + "..."
                test_rect = metrics.boundingRect(QRect(0, 0, available_width, max_height * 10),
                                                Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, test_text)
                if test_rect.height() <= max_height:
                    best_text = test_text
                    low = mid
                else:
                    high = mid - 1
            
            self.display_name_label.setText(best_text)
            self.display_name_label.setToolTip(name)  # Show full text on hover
        else:
            self.display_name_label.setText(name)
            self.display_name_label.setToolTip("")  # No tooltip if text fits

    def resizeEvent(self, event):
        """Handle resize event to update title truncation."""
        super().resizeEvent(event)
        # Update display name truncation when card is resized
        if hasattr(self, 'display_name_label') and self.drive_config.display_name:
            self.update_display_name(self.drive_config.display_name)
    
    def update_remote_name(self, remote_name: str):
        """Update the remote name label."""
        self.drive_config.remote_name = remote_name
        self.remote_name_label.setText(f"Remote: {remote_name}")

    def update_status(self, status: DriveStatus):
        """Update the drive status display."""
        self.drive_status = status
        self.is_updating = False
        self.update_indicator.stop()  # Stop and hide spinner

        if status.error:
            self.status_label.setText(f"Error: {status.error}")
            self.status_label.setStyleSheet(
                "color: #e74c3c; font-size: 13px; font-weight: bold; font-family: 'AtkynsonMono Nerd Font Propo', monospace;"
            )
            self.info_label.setText("Failed to retrieve drive information")
            self.last_updated_str = None
            self.free_space_label.hide()
        else:
            # Store the timestamp string for relative time updates
            self.last_updated_str = status.last_updated
            self._update_relative_time()
            self.status_label.setStyleSheet(
                "color: #27ae60; font-size: 13px; font-weight: bold; font-family: 'AtkynsonMono Nerd Font Propo', monospace;"
            )

            info_text = f"Total: {status.total}\n"
            info_text += f"Used: {status.used}\n"
            info_text += f"Free: {status.free}"
            if status.objects != "Unknown":
                info_text += f"\nObjects: {status.objects}"

            self.info_label.setText(info_text)
            
            # Extract and display free space value at bottom center
            # Extract just the number/value after "Free: " and format to one decimal place
            free_value = status.free
            if free_value and free_value != "Unknown":
                # Parse the value (e.g., "123.456 GB" -> "123.5 GB")
                # Match number with optional decimals and unit
                match = re.match(r'([\d.]+)\s*([A-Za-z]+)?', free_value)
                if match:
                    number_str = match.group(1)
                    unit = match.group(2) if match.group(2) else ""
                    try:
                        number = float(number_str)
                        formatted_number = f"{number:.1f}"
                        formatted_value = f"{formatted_number} {unit}".strip() if unit else formatted_number
                        self.free_space_label.setText(f"Free: {formatted_value}")
                        self.free_space_label.show()
                    except ValueError:
                        # If parsing fails, use original value
                        self.free_space_label.setText(f"Free: {free_value}")
                        self.free_space_label.show()
                else:
                    # If no match, use original value
                    self.free_space_label.setText(f"Free: {free_value}")
                    self.free_space_label.show()
            else:
                self.free_space_label.hide()

    def _update_relative_time(self):
        """Update the status label with relative time if we have a last_updated timestamp."""
        if self.last_updated_str and not self.is_updating:
            relative_time = format_relative_time(self.last_updated_str)
            self.status_label.setText(f"Last updated: {relative_time}")

    def set_updating(self, is_updating: bool):
        """Set updating state with animation."""
        self.is_updating = is_updating
        if is_updating:
            self.status_label.setText("Updating...")
            self.status_label.setStyleSheet(
                "color: #f39c12; font-size: 13px; font-weight: bold; font-family: 'AtkynsonMono Nerd Font Propo', monospace;"
            )
            self.update_indicator.show()
            self.update_indicator.start()  # Start the spinner animation
            self.update_spacer.hide()  # Hide spacer to show indicator
        else:
            self.update_indicator.stop()  # Stop the spinner
            self.update_indicator.hide()  # Hide the spinner
            self.update_spacer.show()  # Show spacer to maintain layout
            # Update relative time when done updating
            if self.last_updated_str:
                self._update_relative_time()

    def mousePressEvent(self, event):
        """Handle mouse press for drag initiation."""
        # Only start drag if not clicking on an editable field
        clicked_widget = self.childAt(event.position().toPoint())
        if isinstance(clicked_widget, QLineEdit):
            # Let the line edit handle the event
            super().mousePressEvent(event)
            return

        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move to initiate drag."""
        if not (event.buttons() & Qt.LeftButton):
            super().mouseMoveEvent(event)
            return

        # Check if we've moved enough to start a drag
        if (
            event.position().toPoint() - self.drag_start_position
        ).manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        # Create drag
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.drive_config.remote_name)
        drag.setMimeData(mime_data)

        # Create drag pixmap
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        # Render the widget to the pixmap with correct signature
        self.render(painter, QPoint(0, 0))
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.position().toPoint())

        # Set dragging state
        self.setProperty("dragging", True)
        self.style().unpolish(self)
        self.style().polish(self)

        # Execute drag
        drag.exec(Qt.MoveAction)

        # Reset dragging state
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)

        event.accept()

    def _store_content_state(self):
        """Store the current card's content state for restoration."""
        state = {
            'display_name': self.drive_config.display_name,
            'status_text': self.status_label.text() if hasattr(self, 'status_label') else '',
            'status_style': self.status_label.styleSheet() if hasattr(self, 'status_label') else '',
            'info_text': self.info_label.text() if hasattr(self, 'info_label') else '',
            'free_space_text': self.free_space_label.text() if hasattr(self, 'free_space_label') else '',
            'free_space_visible': self.free_space_label.isVisible() if hasattr(self, 'free_space_label') else False,
            'remote_name': self.drive_config.remote_name,
            'icon_pixmap': self.icon_label.pixmap() if hasattr(self, 'icon_label') and self.icon_label.pixmap() else None,
            'drive_status': self.drive_status,
            'is_updating': self.is_updating,
            'last_updated_str': self.last_updated_str,
        }
        return state
    
    def _copy_content_from(self, source_card):
        """Copy content from another card to this card."""
        if not source_card:
            return
        
        # Store original state if not already stored
        if self._original_content_state is None:
            self._original_content_state = self._store_content_state()
        
        # Copy display name
        self.drive_config.display_name = source_card.drive_config.display_name
        self.update_display_name(source_card.drive_config.display_name)
        
        # Copy status
        if hasattr(source_card, 'status_label') and hasattr(self, 'status_label'):
            self.status_label.setText(source_card.status_label.text())
            self.status_label.setStyleSheet(source_card.status_label.styleSheet())
        
        # Copy info
        if hasattr(source_card, 'info_label') and hasattr(self, 'info_label'):
            self.info_label.setText(source_card.info_label.text())
        
        # Copy free space
        if hasattr(source_card, 'free_space_label') and hasattr(self, 'free_space_label'):
            self.free_space_label.setText(source_card.free_space_label.text())
            if source_card.free_space_label.isVisible():
                self.free_space_label.show()
            else:
                self.free_space_label.hide()
        
        # Copy remote name
        self.drive_config.remote_name = source_card.drive_config.remote_name
        if hasattr(source_card, 'remote_name_label') and hasattr(self, 'remote_name_label'):
            self.remote_name_label.setText(source_card.remote_name_label.text())
        
        # Copy icon
        if hasattr(source_card, 'icon_label') and hasattr(self, 'icon_label'):
            if source_card.icon_label.pixmap():
                self.icon_label.setPixmap(source_card.icon_label.pixmap())
        
        # Copy status object
        self.drive_status = source_card.drive_status
        self.is_updating = source_card.is_updating
        self.last_updated_str = source_card.last_updated_str
        
        # Update update indicator
        if source_card.is_updating:
            self.set_updating(True)
        else:
            self.set_updating(False)
    
    def _restore_content_state(self):
        """Restore the card's original content state."""
        if self._original_content_state is None:
            return
        
        state = self._original_content_state
        
        # Restore display name
        self.drive_config.display_name = state['display_name']
        self.update_display_name(state['display_name'])
        
        # Restore status
        if hasattr(self, 'status_label'):
            self.status_label.setText(state['status_text'])
            self.status_label.setStyleSheet(state['status_style'])
        
        # Restore info
        if hasattr(self, 'info_label'):
            self.info_label.setText(state['info_text'])
        
        # Restore free space
        if hasattr(self, 'free_space_label'):
            self.free_space_label.setText(state['free_space_text'])
            if state['free_space_visible']:
                self.free_space_label.show()
            else:
                self.free_space_label.hide()
        
        # Restore remote name
        self.drive_config.remote_name = state['remote_name']
        if hasattr(self, 'remote_name_label'):
            self.remote_name_label.setText(f"Remote: {state['remote_name']}")
        
        # Restore icon
        if hasattr(self, 'icon_label') and state['icon_pixmap']:
            self.icon_label.setPixmap(state['icon_pixmap'])
        
        # Restore status object
        self.drive_status = state['drive_status']
        self.is_updating = state['is_updating']
        self.last_updated_str = state.get('last_updated_str')
        
        # Restore update indicator
        if state['is_updating']:
            self.set_updating(True)
        else:
            self.set_updating(False)
        
        # Clear stored state
        self._original_content_state = None
        self._preview_target_card = None

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasText() and event.mimeData().text() != self.drive_config.remote_name:
            event.acceptProposedAction()
            dragged_remote = event.mimeData().text()
            
            # Find the card being dragged
            dragged_card = None
            parent = self.parent()
            while parent:
                if hasattr(parent, "drive_cards"):
                    dragged_card = parent.drive_cards.get(dragged_remote)
                    break
                parent = parent.parent()
            
            if dragged_card:
                # Store the dragged card's original content if not already stored
                if dragged_card._original_content_state is None:
                    dragged_card._original_content_state = dragged_card._store_content_state()
                    dragged_card._preview_target_card = self
                
                # Copy this card's content to the dragged card (preview)
                dragged_card._copy_content_from(self)
            
            # Store current height and set fixed height to maintain card size (like edit mode)
            current_height = self.sizeHint().height()
            if current_height <= 0:
                current_height = self.height()
            if current_height > 0:
                self._drag_over_height = current_height
                self.setFixedHeight(current_height)
            
            # Hide all content widgets (like edit mode does)
            if hasattr(self, 'icon_label'):
                self.icon_label.hide()
            if hasattr(self, 'header_layout_widget'):
                self.header_layout_widget.hide()
            if hasattr(self, 'status_label'):
                self.status_label.hide()
            if hasattr(self, 'info_label'):
                self.info_label.hide()
            if hasattr(self, 'free_space_label'):
                self.free_space_label.hide()
            if hasattr(self, 'settings_button'):
                self.settings_button.hide()
            if hasattr(self, 'update_spacer'):
                self.update_spacer.hide()
            if hasattr(self, 'remote_name_label'):
                self.remote_name_label.hide()
            if hasattr(self, 'update_indicator'):
                self.update_indicator.hide()
            if hasattr(self, 'name_container'):
                self.name_container.hide()
            
            # Set grey background to show it's a drop target
        self.setStyleSheet("""
            QFrame {
                    background-color: #e0e0e0;
                    border: 2px solid #bdc3c7;
                border-radius: 12px;
                    padding: 4px 6px;
                margin: 4px;
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
            """)

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        # Restore height constraints (like exit edit mode)
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX equivalent
        self._drag_over_height = None
        
        # Restore original appearance - show all content and restore stylesheet
        if hasattr(self, 'icon_label'):
            self.icon_label.show()
        if hasattr(self, 'header_layout_widget'):
            self.header_layout_widget.show()
        if hasattr(self, 'status_label'):
            self.status_label.show()
        if hasattr(self, 'info_label'):
            self.info_label.show()
        if hasattr(self, 'free_space_label'):
            self.free_space_label.show()
        if hasattr(self, 'settings_button'):
            self.settings_button.show()
        if hasattr(self, 'update_spacer'):
            self.update_spacer.show()
        if hasattr(self, 'remote_name_label'):
            self.remote_name_label.show()
        if hasattr(self, 'update_indicator') and self.is_updating:
            self.update_indicator.show()
        if hasattr(self, 'name_container'):
            self.name_container.show()
        # Restore original stylesheet
        self.setStyleSheet(self._original_stylesheet)
        
        # Restore the dragged card's original content if it was showing preview
        if event.mimeData().hasText():
            dragged_remote = event.mimeData().text()
            parent = self.parent()
            while parent:
                if hasattr(parent, "drive_cards"):
                    dragged_card = parent.drive_cards.get(dragged_remote)
                    if dragged_card and dragged_card._preview_target_card == self:
                        dragged_card._restore_content_state()
                    break
                parent = parent.parent()

    def dropEvent(self, event):
        """Handle drop event."""
        dragged_remote = None
        if event.mimeData().hasText():
            dragged_remote = event.mimeData().text()
            if dragged_remote != self.drive_config.remote_name:
                # Notify parent to handle reordering
                parent = self.parent()
                while parent:
                    if hasattr(parent, "reorder_cards"):
                        parent.reorder_cards(dragged_remote, self.drive_config.remote_name)
                        break
                    parent = parent.parent()
            event.acceptProposedAction()

        # Restore height constraints (like exit edit mode)
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX equivalent
        self._drag_over_height = None
        
        # Restore original appearance - show all content and restore stylesheet
        if hasattr(self, 'icon_label'):
            self.icon_label.show()
        if hasattr(self, 'header_layout_widget'):
            self.header_layout_widget.show()
        if hasattr(self, 'status_label'):
            self.status_label.show()
        if hasattr(self, 'info_label'):
            self.info_label.show()
        if hasattr(self, 'free_space_label'):
            self.free_space_label.show()
        if hasattr(self, 'settings_button'):
            self.settings_button.show()
        if hasattr(self, 'update_spacer'):
            self.update_spacer.show()
        if hasattr(self, 'remote_name_label'):
            self.remote_name_label.show()
        if hasattr(self, 'update_indicator') and self.is_updating:
            self.update_indicator.show()
        if hasattr(self, 'name_container'):
            self.name_container.show()
        # Restore original stylesheet
        self.setStyleSheet(self._original_stylesheet)
        
        # Restore the dragged card's original content (drop completed, so restore preview)
        if dragged_remote:
            parent = self.parent()
            while parent:
                if hasattr(parent, "drive_cards"):
                    dragged_card = parent.drive_cards.get(dragged_remote)
                    if dragged_card and dragged_card._preview_target_card == self:
                        dragged_card._restore_content_state()
                    break
                parent = parent.parent()
