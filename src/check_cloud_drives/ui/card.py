"""Drive card UI component."""

from datetime import datetime

from PySide6.QtCore import Property, QEasingCurve, QMimeData, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor, QDrag, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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

    def __init__(self, drive_config: DriveConfig, parent=None):
        super().__init__(parent)
        self.drive_config = drive_config
        self.drive_status: DriveStatus | None = None
        self.is_updating = False
        self.drag_start_position = QPoint()
        self.setAcceptDrops(True)  # Enable drop events
        self.last_updated_str: str | None = None  # Store last updated timestamp string
        # Timer to update relative time every minute
        self.time_update_timer = QTimer(self)
        self.time_update_timer.timeout.connect(self._update_relative_time)
        self.time_update_timer.start(60000)  # Update every 60 seconds (1 minute)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI for the drive card."""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 12px;
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

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header with icon and name
        header_layout = QHBoxLayout()

        # Icon (will load SVG if available, otherwise placeholder)
        icon_label = QLabel()
        icon_size = 52  # Optimal size for visibility without being too large
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setMinimumSize(icon_size, icon_size)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setScaledContents(True)  # Allow pixmap to scale within label
        # Remove any default styling that might create borders or backgrounds
        icon_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        icon_pixmap = load_icon(self.drive_config.drive_type, size=icon_size)
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap)
        self.icon_label = icon_label

        # Name and remote name labels
        name_layout = QVBoxLayout()
        # Display name as non-editable title label (centered)
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
        self.display_name_label.setAlignment(Qt.AlignCenter)
        name_layout.addWidget(self.display_name_label)

        # Remote name as non-editable label with "Remote: " prefix
        self.remote_name_label = QLabel(f"Remote: {self.drive_config.remote_name}")
        self.remote_name_label.setStyleSheet("""
            QLabel {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 11px;
                color: #7f8c8d;
                background-color: transparent;
                border: none;
                padding: 2px 0px;
            }
        """)
        self.remote_name_label.setAlignment(Qt.AlignCenter)
        name_layout.addWidget(self.remote_name_label)

        header_layout.addWidget(icon_label)
        header_layout.addLayout(name_layout, 1)

        layout.addLayout(header_layout)

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

        # Bottom section with update indicator and settings icon
        bottom_layout = QHBoxLayout()

        # Update indicator at bottom left (shows animated spinner when updating)
        self.update_indicator = LoadingSpinner(self, size=32, color="#f39c12")
        self.update_indicator.setToolTip(
            "Update status indicator - shows when drive is being refreshed"
        )
        self.update_indicator.hide()  # Hidden by default
        bottom_layout.addWidget(self.update_indicator)

        bottom_layout.addStretch()

        # Settings icon (Nerd Font) at bottom right
        settings_icon = QLabel("\uf013")  # nf-fa-cog (gear icon)
        settings_icon.setStyleSheet("""
            QLabel {
                color: #5a6c7d;
                font-size: 24px;
                font-family: 'AtkynsonMono Nerd Font Propo', monospace;
                background-color: transparent;
                padding: 0px;
                margin: 0px;
                border: none;
            }
        """)
        settings_icon.setToolTip("Settings")
        settings_icon.setFixedSize(32, 32)  # Match update indicator size
        settings_icon.setMinimumSize(32, 32)
        settings_icon.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        settings_icon.setScaledContents(False)
        self.settings_icon = settings_icon
        bottom_layout.addWidget(settings_icon)

        layout.addLayout(bottom_layout)

    def update_display_name(self, name: str):
        """Update the display name label."""
        self.drive_config.display_name = name
        self.display_name_label.setText(name)

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
            self.update_indicator.start()  # Start the spinner animation
        else:
            self.update_indicator.stop()  # Stop and hide the spinner
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

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasText() and event.mimeData().text() != self.drive_config.remote_name:
            event.acceptProposedAction()
            # Visual feedback
            self.setStyleSheet(
                self.styleSheet()
                + """
                QFrame {
                    border-color: #4a90e2;
                    border-width: 3px;
                }
            """
            )

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        # Reset visual feedback - restore original border
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 12px;
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

    def dropEvent(self, event):
        """Handle drop event."""
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

        # Reset visual feedback - restore original border
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 12px;
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
