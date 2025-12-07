"""Main application window."""

import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QIcon,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from ..config import ConfigManager
from ..models import DriveConfig, DriveStatus
from ..rclone import RcloneWorker
from .card import DriveCard
from .dialogs import SetupDialog


class StackedIconButton(QPushButton):
    """Button with stacked icons - cloud icon with plus icon on top."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # Nerd Font Unicode codepoints (Private Use Area)
        # nf-md-cloud: U+F0C2, nf-fa-plus: U+F067
        self.cloud_icon = "\uf0c2"  # nf-md-cloud
        self.plus_icon = "\uf067"  # nf-fa-plus

    def paintEvent(self, event):
        """Custom paint to draw stacked icons."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get button rect
        rect = self.rect()
        center_x = rect.center().x()
        center_y = rect.center().y()

        # Draw cloud icon (larger, base, inverted/white)
        font = QFont("AtkynsonMono Nerd Font Propo", 22)  # Larger size
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))  # Inverted (white)
        painter.drawText(rect, Qt.AlignCenter, self.cloud_icon)

        # Draw plus icon (smaller, blue color matching button, on top)
        font_small = QFont("AtkynsonMono Nerd Font Propo", 14)  # Larger size
        painter.setFont(font_small)
        painter.setPen(QColor("#4a90e2"))  # Blue color matching button background
        # Position plus icon centered on cloud, moved up a little
        plus_rect = QRect(center_x - 12, center_y - 10, 24, 24)  # Moved up by 2 pixels
        painter.drawText(plus_rect, Qt.AlignCenter, self.plus_icon)


class DropTargetWidget(QWidget):
    """Widget that accepts drops for card reordering."""

    def __init__(self, parent=None, reorder_callback=None):
        super().__init__(parent)
        self.reorder_callback = reorder_callback
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event - find the card under the drop position."""
        if not event.mimeData().hasText():
            return

        dragged_remote = event.mimeData().text()
        drop_pos = event.position().toPoint()

        # Find which card (if any) is under the drop position
        target_card = None
        for child in self.findChildren(DriveCard):
            if child.geometry().contains(drop_pos):
                target_card = child
                break

        if target_card and self.reorder_callback:
            target_remote = target_card.drive_config.remote_name
            if dragged_remote != target_remote:
                self.reorder_callback(dragged_remote, target_remote)

        event.acceptProposedAction()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        # Config file in project root directory
        project_root = Path(__file__).parent.parent.parent.parent
        config_path = project_root / "CheckCloudDrivesConfig.toml"
        self.config_manager = ConfigManager(config_path)
        self.drive_cards: dict[str, DriveCard] = {}
        self.workers: list[RcloneWorker] = []
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_drives)
        self.standard_button_height = None  # Will be set in _setup_ui

        self._setup_ui()
        self._setup_tray()
        self._load_drives()
        self._restore_geometry()

        # Auto-refresh
        interval = self.config_manager.config.get("auto_refresh_interval", 300)
        if interval > 0:
            self.refresh_timer.start(interval * 1000)

    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("Check Cloud Drives")
        # Calculate optimal width for drive cards:
        # - Card max width: 400px
        # - Layout margins: 12px on each side = 24px total
        # - Scrollbar width: ~17px (when scrolling is needed)
        # - Extra padding: ~10px for safety
        # Total: 400 + 24 + 17 + 10 = 451px, round to 450px
        optimal_width = 450
        self.setMinimumSize(optimal_width, 300)
        self.resize(optimal_width, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Title (draggable area)
        title = QLabel("Cloud Drive Status")
        title.setStyleSheet("""
            font-family: "AtkynsonMono Nerd Font Propo", monospace;
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 8px;
            background-color: #ecf0f1;
            border-radius: 6px;
        """)
        title.setAlignment(Qt.AlignCenter)
        title.mousePressEvent = lambda e: self._title_mouse_press(e)
        title.mouseMoveEvent = lambda e: self._title_mouse_move(e)
        title.mouseReleaseEvent = lambda e: self._title_mouse_release(e)
        self.title_label = title
        layout.addWidget(title)

        # Scroll area for drive cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
        """)

        scroll_widget = DropTargetWidget(self, self.reorder_cards)
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(4)
        scroll_layout.addStretch()

        self.cards_container = scroll_widget
        self.cards_layout = scroll_layout

        scroll.setWidget(scroll_widget)

        # Calculate standard button height first (needed for settings page buttons)
        # Create a reference button to get standard height (matching dialog buttons)
        # Use same styling as dialog buttons: padding 6px 12px, font-size 12px, font-weight bold
        ref_button = QPushButton("Cancel")
        ref_button.setStyleSheet("""
            QPushButton {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
        """)
        self.standard_button_height = ref_button.sizeHint().height()
        ref_button.deleteLater()

        # Settings page (initially hidden)
        self.settings_page = self._create_settings_page()
        self.settings_page.hide()

        # Store reference to scroll area
        self.scroll_area = scroll

        # Stack widgets to switch between cards and settings
        self.content_stack = QWidget()
        content_stack_layout = QVBoxLayout(self.content_stack)
        content_stack_layout.setContentsMargins(0, 0, 0, 0)
        content_stack_layout.setSpacing(0)
        content_stack_layout.addWidget(scroll)
        content_stack_layout.addWidget(self.settings_page)

        layout.addWidget(self.content_stack)

        # Control buttons
        controls = QHBoxLayout()

        # Refresh All button with nf-md-cloud_refresh icon
        # nf-md-cloud_refresh: U+F052A (codepoint f052a from nerdfonts.com)
        # Using the actual character provided by user: 󰔪
        refresh_btn = QPushButton("󰔪")  # nf-md-cloud_refresh
        refresh_btn.setStyleSheet("""
            QPushButton {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 26px;
                min-width: 45px;
                max-width: 45px;
                min-height: 32px;
                max-height: 32px;
                padding: 4px;
            }
        """)
        refresh_btn.setToolTip("Refresh All")
        refresh_btn.clicked.connect(self.refresh_all_drives)
        controls.addWidget(refresh_btn)

        # Add Drive button with stacked icons (cloud + plus)
        add_btn = StackedIconButton("")
        add_btn.setStyleSheet("""
            QPushButton {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                min-width: 45px;
                max-width: 45px;
                min-height: 32px;
                max-height: 32px;
                padding: 4px;
            }
        """)
        add_btn.setToolTip("Add Drive")
        add_btn.clicked.connect(self._add_drive)
        controls.addWidget(add_btn)

        settings_btn = QPushButton("\uf013")  # nf-fa-cog (gear icon) - same as cards
        settings_btn.setStyleSheet("""
            QPushButton {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 22px;
                min-width: 45px;
                max-width: 45px;
                min-height: 32px;
                max-height: 32px;
                padding: 4px;
            }
        """)
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._show_settings)
        controls.addWidget(settings_btn)

        controls.addStretch()

        # Hide button (blue) - same font and height as dialog buttons
        hide_btn = QPushButton("Hide")
        hide_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                font-weight: bold;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: {self.standard_button_height}px;
                max-height: {self.standard_button_height}px;
                height: {self.standard_button_height}px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
            QPushButton:pressed {{
                background-color: #21618c;
            }}
        """)
        hide_btn.setFixedHeight(self.standard_button_height)
        hide_btn.clicked.connect(self.hide)
        controls.addWidget(hide_btn, alignment=Qt.AlignVCenter)

        # Exit button (red) - same font and height as dialog buttons
        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                font-weight: bold;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: {self.standard_button_height}px;
                max-height: {self.standard_button_height}px;
                height: {self.standard_button_height}px;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
            QPushButton:pressed {{
                background-color: #a93226;
            }}
        """)
        exit_btn.setFixedHeight(self.standard_button_height)
        exit_btn.clicked.connect(QApplication.quit)
        controls.addWidget(exit_btn, alignment=Qt.AlignVCenter)

        layout.addLayout(controls)

        # Create overlay for dimming when dialog is shown
        # Overlay covers the entire central widget
        self.overlay = QWidget(central)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.overlay.hide()
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # Block mouse events
        self.overlay.lower()  # Start below other widgets

        # Apply light theme with AtkynsonMono Nerd Font Propo
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2a6ba0;
            }
            QLabel {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
            QLineEdit {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
            QListWidget {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
            QDialog {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
        """)

        # Track mouse for edge snapping
        self.edge_snap_threshold = 20  # pixels
        self.is_dragging = False
        self.drag_position = QPoint()

    def _setup_tray(self):
        """Set up system tray icon."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(
                self, "System Tray", "System tray is not available on this system."
            )
            return

        self.tray_icon = QSystemTrayIcon(self)

        # Create a simple icon (placeholder - you can replace with actual icon)
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(100, 150, 255))
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 20))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "☁")
        painter.end()

        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip("Check Cloud Drives")

        # Tray menu
        tray_menu = QMenu(self)

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        stay_on_top_action = QAction("Stay on Top", self)
        stay_on_top_action.setCheckable(True)
        stay_on_top_action.setChecked(self.config_manager.get_stay_on_top())
        stay_on_top_action.triggered.connect(self._toggle_stay_on_top)
        tray_menu.addAction(stay_on_top_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()

    def _toggle_stay_on_top(self, checked: bool):
        """Toggle stay on top window flag."""
        self.config_manager.set_stay_on_top(checked)
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def _load_drives(self):
        """Load drives from config and set up UI in saved order."""
        drives = self.config_manager.get_drives()
        if not drives:
            # First run - show setup dialog
            self._first_run_setup()
        else:
            # Load drives in saved order
            saved_order = self.config_manager.get_drive_order()
            drives_dict = {d.remote_name: d for d in drives if d.enabled}

            # Add drives in saved order, then any remaining drives
            ordered_drives = []
            for remote_name in saved_order:
                if remote_name in drives_dict:
                    ordered_drives.append(drives_dict[remote_name])
                    del drives_dict[remote_name]

            # Add any remaining drives that weren't in saved order
            for drive_config in drives_dict.values():
                ordered_drives.append(drive_config)

            # Add cards in order
            for drive_config in ordered_drives:
                self._add_drive_card(drive_config)

            # Auto-refresh on load
            QTimer.singleShot(1000, self.refresh_all_drives)

    def _first_run_setup(self):
        """Handle first run setup."""
        available_remotes = self._get_available_remotes()
        if available_remotes:
            drive_order = []  # Empty for first run
            self._show_overlay()
            dialog = SetupDialog(available_remotes, [], drive_order, self)
            result = dialog.exec()
            self._hide_overlay()
            if result == QDialog.Accepted:
                for drive_config in dialog.selected_drives:
                    self._add_drive_card(drive_config)
                self._save_drives()
                QTimer.singleShot(1000, self.refresh_all_drives)
        else:
            QMessageBox.information(
                self, "No Remotes Found", "No rclone remotes found. Please configure rclone first."
            )

    def _get_available_remotes(self) -> list[str]:
        """Get list of available rclone remotes."""
        try:
            # Check if rclone is available
            subprocess.run(["rclone", "version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            QMessageBox.critical(
                self,
                "rclone Not Found",
                "rclone is not installed or not in PATH.\n\n"
                "Please install rclone from https://rclone.org/install/",
            )
            return []
        except Exception:
            pass  # Continue anyway

        try:
            result = subprocess.run(
                ["rclone", "listremotes"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                remotes = [
                    line.strip().rstrip(":")
                    for line in result.stdout.strip().split("\n")
                    if line.strip()
                ]
                return remotes
        except Exception as e:
            print(f"Error getting remotes: {e}")
        return []

    def _add_drive(self):
        """Add a new drive."""
        available_remotes = self._get_available_remotes()
        existing_drives = self.config_manager.get_drives()
        drive_order = self.config_manager.get_drive_order()
        self._show_overlay()
        dialog = SetupDialog(available_remotes, existing_drives, drive_order, self)
        result = dialog.exec()
        self._hide_overlay()
        if result == QDialog.Accepted:
            # Get list of selected remote names
            selected_remote_names = {d.remote_name for d in dialog.selected_drives}
            existing_remote_names = set(self.drive_cards.keys())
            
            # Remove drives that are not in the selected list (unchecked)
            for remote_name in list(self.drive_cards.keys()):
                if remote_name not in selected_remote_names:
                    card = self.drive_cards[remote_name]
                    # Remove from layout
                    self.cards_layout.removeWidget(card)
                    card.deleteLater()
                    # Remove from dict
                    del self.drive_cards[remote_name]
            
            # Create a dict of selected drives for lookup
            selected_drives_dict = {d.remote_name: d for d in dialog.selected_drives}
            
            # Separate existing drives from new drives
            existing_drives = []
            new_drives = []
            
            for drive_config in dialog.selected_drives:
                if drive_config.remote_name in existing_remote_names:
                    existing_drives.append(drive_config)
                else:
                    new_drives.append(drive_config)
            
            # Update existing cards (they stay in their current positions)
            for drive_config in existing_drives:
                if drive_config.remote_name in self.drive_cards:
                    # Update card config if needed
                    self.drive_cards[drive_config.remote_name].drive_config = drive_config
            
            # Add new drives at the bottom (before the stretch)
            for drive_config in new_drives:
                self._add_drive_card(drive_config)
            
            # Save the updated drive list (only selected drives) and order
            self.config_manager.set_drives(dialog.selected_drives)
            self._save_drive_order()
            self.refresh_all_drives()

    def _add_drive_card(self, drive_config: DriveConfig):
        """Add a drive card to the UI."""
        if drive_config.remote_name in self.drive_cards:
            return  # Already exists

        card = DriveCard(drive_config, self.cards_container)
        card.setAcceptDrops(True)
        # Connect signal to save display name changes to config
        card.display_name_saved.connect(lambda name, remote=drive_config.remote_name: self._save_card_display_name(remote, name))
        # Connect signal to remove card
        card.card_removed.connect(lambda remote=drive_config.remote_name: self._remove_card(remote))
        self.drive_cards[drive_config.remote_name] = card

        # Insert before stretch
        count = self.cards_layout.count()
        self.cards_layout.insertWidget(count - 1, card)

    def _save_card_display_name(self, remote_name: str, display_name: str):
        """Save the display name for a specific drive card."""
        # Update the drive config in the config manager
        drives = self.config_manager.get_drives()
        for drive in drives:
            if drive.remote_name == remote_name:
                drive.display_name = display_name
                break
        self.config_manager.set_drives(drives)
        self.config_manager.save_config()
    
    def _remove_card(self, remote_name: str):
        """Remove a card from the UI and config."""
        if remote_name not in self.drive_cards:
            return
        
        card = self.drive_cards[remote_name]
        
        # Remove card from layout
        self.cards_layout.removeWidget(card)
        card.deleteLater()
        
        # Remove from dict
        del self.drive_cards[remote_name]
        
        # Update config - remove the drive from the list
        drives = self.config_manager.get_drives()
        drives = [d for d in drives if d.remote_name != remote_name]
        self.config_manager.set_drives(drives)
        self.config_manager.save_config()
        
        # Update drive order
        self._save_drive_order()
    
    def _save_drives(self):
        """Save current drives to config."""
        drives = []
        for card in self.drive_cards.values():
            drives.append(card.drive_config)
        self.config_manager.set_drives(drives)
        self._save_drive_order()

    def _save_drive_order(self):
        """Save the current order of drive cards."""
        order = []
        # The stretch is at the end, so iterate all items except the last one
        for i in range(self.cards_layout.count() - 1):  # Exclude stretch at the end
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                card = item.widget()
                if isinstance(card, DriveCard):
                    order.append(card.drive_config.remote_name)
        self.config_manager.set_drive_order(order)

    def reorder_cards(self, dragged_remote: str, target_remote: str):
        """Reorder cards when one is dragged onto another."""
        if dragged_remote == target_remote:
            return

        if dragged_remote not in self.drive_cards or target_remote not in self.drive_cards:
            return

        dragged_card = self.drive_cards[dragged_remote]
        target_card = self.drive_cards[target_remote]

        # Get current positions (these indices account for the stretch at index 0)
        dragged_index = self.cards_layout.indexOf(dragged_card)
        target_index = self.cards_layout.indexOf(target_card)

        if dragged_index == -1 or target_index == -1:
            return

        # Remove dragged card first
        self.cards_layout.removeWidget(dragged_card)

        # Calculate insert position
        # After removing the dragged card, indices shift:
        # - If moving down (dragged_index < target_index), target_index decreases by 1
        # - If moving up (dragged_index > target_index), target_index stays the same
        if dragged_index < target_index:
            # Moving down - insert after target
            # After removal, target is at (target_index - 1), so insert at target_index
            insert_index = target_index
        else:
            # Moving up - insert before target (target_index unchanged after removal)
            insert_index = target_index

        # Reinsert at the correct position
        self.cards_layout.insertWidget(insert_index, dragged_card)

        # Force layout update to ensure visual change
        self.cards_layout.update()

        # Save new order
        self._save_drive_order()

    def refresh_all_drives(self):
        """Refresh status for all drives."""
        for card in self.drive_cards.values():
            self._refresh_drive(card)

    def _refresh_drive(self, card: DriveCard):
        """Refresh status for a single drive."""
        remote_name = card.drive_config.remote_name
        if not remote_name:
            return

        card.set_updating(True)

        worker = RcloneWorker(["rclone", "about", remote_name + ":"], remote_name)
        worker.finished.connect(lambda rn, result: self._on_drive_update(rn, result, None))
        worker.error.connect(lambda rn, error: self._on_drive_update(rn, None, error))
        worker.start()
        self.workers.append(worker)

    def _on_drive_update(self, remote_name: str, result: dict | None, error: str | None):
        """Handle drive update result."""
        if remote_name not in self.drive_cards:
            return

        card = self.drive_cards[remote_name]
        card.set_updating(False)

        if error:
            status = DriveStatus(remote_name=remote_name, error=error)
        else:
            status = DriveStatus(
                remote_name=remote_name,
                total=result.get("total", "Unknown"),
                used=result.get("used", "Unknown"),
                free=result.get("free", "Unknown"),
                trash=result.get("trash", "Unknown"),
                other=result.get("other", "Unknown"),
                objects=result.get("objects", "Unknown"),
                last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

        card.update_status(status)
        self._save_drives()

    def _create_settings_page(self) -> QWidget:
        """Create the settings page widget."""
        settings_widget = QWidget()
        settings_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                margin: 4px;
            }
        """)
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(12)
        settings_layout.setContentsMargins(20, 20, 20, 12)

        # Title
        title = QLabel("App Settings")
        title.setStyleSheet("""
            font-family: "AtkynsonMono Nerd Font Propo", monospace;
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 8px 0px;
        """)
        settings_layout.addWidget(title)

        # Auto-refresh settings
        refresh_group = QGroupBox("Auto-Refresh")
        refresh_group.setStyleSheet("""
            QGroupBox {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        refresh_layout = QVBoxLayout(refresh_group)

        self.auto_refresh_enabled = QCheckBox("Enable auto-refresh")
        self.auto_refresh_enabled.setStyleSheet("""
            QCheckBox {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                color: #2c3e50;
            }
        """)
        refresh_layout.addWidget(self.auto_refresh_enabled)

        interval_layout = QHBoxLayout()
        interval_label = QLabel("Refresh interval (minutes):")
        interval_label.setStyleSheet(
            "font-family: 'AtkynsonMono Nerd Font Propo', monospace; font-size: 12px; color: #2c3e50;"
        )
        interval_layout.addWidget(interval_label)

        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setMinimum(1)
        self.refresh_interval_spin.setMaximum(1440)  # Max 24 hours
        self.refresh_interval_spin.setSuffix(" min")
        self.refresh_interval_spin.setStyleSheet("""
            QSpinBox {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                padding: 4px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
            QSpinBox::up-button {
                background-color: #ecf0f1;
                border: 1px solid #d0d0d0;
                border-top-right-radius: 4px;
                width: 20px;
                subcontrol-origin: border;
                subcontrol-position: top right;
            }
            QSpinBox::up-button:hover {
                background-color: #bdc3c7;
            }
            QSpinBox::up-button:pressed {
                background-color: #95a5a6;
            }
            QSpinBox::down-button {
                background-color: #ecf0f1;
                border: 1px solid #d0d0d0;
                border-bottom-right-radius: 4px;
                width: 20px;
                subcontrol-origin: border;
                subcontrol-position: bottom right;
            }
            QSpinBox::down-button:hover {
                background-color: #bdc3c7;
            }
            QSpinBox::down-button:pressed {
                background-color: #95a5a6;
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid #2c3e50;
                width: 0px;
                height: 0px;
                margin-left: 2px;
                margin-right: 2px;
            }
            QSpinBox::up-arrow:hover {
                border-bottom-color: #1a252f;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #2c3e50;
                width: 0px;
                height: 0px;
                margin-left: 2px;
                margin-right: 2px;
            }
            QSpinBox::down-arrow:hover {
                border-top-color: #1a252f;
            }
        """)
        interval_layout.addWidget(self.refresh_interval_spin)
        interval_layout.addStretch()
        refresh_layout.addLayout(interval_layout)

        settings_layout.addWidget(refresh_group)

        # Window settings
        window_group = QGroupBox("Window Behavior")
        window_group.setStyleSheet("""
            QGroupBox {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        window_layout = QVBoxLayout(window_group)

        self.stay_on_top_check = QCheckBox("Keep window on top")
        self.stay_on_top_check.setStyleSheet("""
            QCheckBox {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                color: #2c3e50;
            }
        """)
        window_layout.addWidget(self.stay_on_top_check)

        self.run_at_startup_check = QCheckBox("Run at system startup")
        self.run_at_startup_check.setStyleSheet("""
            QCheckBox {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                color: #2c3e50;
            }
        """)
        window_layout.addWidget(self.run_at_startup_check)

        settings_layout.addWidget(window_group)

        # Config file path
        config_path_label = QLabel(f"Config file: {self.config_manager.config_path}")
        config_path_label.setStyleSheet("""
            QLabel {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 11px;
                color: #7f8c8d;
                background-color: transparent;
                border: none;
                padding: 8px 0px;
            }
        """)
        config_path_label.setWordWrap(True)
        settings_layout.addWidget(config_path_label)

        settings_layout.addStretch()

        # Save and Cancel buttons (centered)
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Use the exact same height as Hide/Exit buttons
        # Use self.standard_button_height which was calculated earlier in _setup_ui
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                font-weight: bold;
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: {self.standard_button_height}px;
                max-height: {self.standard_button_height}px;
                height: {self.standard_button_height}px;
            }}
            QPushButton:hover {{
                background-color: #7f8c8d;
            }}
            QPushButton:pressed {{
                background-color: #6c7a7b;
            }}
        """)
        cancel_btn.setFixedHeight(self.standard_button_height)
        cancel_btn.clicked.connect(self._cancel_settings)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                font-weight: bold;
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: {self.standard_button_height}px;
                max-height: {self.standard_button_height}px;
                height: {self.standard_button_height}px;
            }}
            QPushButton:hover {{
                background-color: #229954;
            }}
            QPushButton:pressed {{
                background-color: #1e8449;
            }}
        """)
        save_btn.setFixedHeight(self.standard_button_height)
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()

        settings_layout.addLayout(button_layout)

        return settings_widget

    def _show_settings(self):
        """Show settings page."""
        # Load current settings
        auto_refresh_interval = self.config_manager.config.get("auto_refresh_interval", 300)
        stay_on_top = self.config_manager.config.get("stay_on_top", False)
        run_at_startup = self.config_manager.config.get("run_at_startup", False)

        self.auto_refresh_enabled.setChecked(auto_refresh_interval > 0)
        self.refresh_interval_spin.setValue(
            auto_refresh_interval // 60
        )  # Convert seconds to minutes
        self.stay_on_top_check.setChecked(stay_on_top)
        self.run_at_startup_check.setChecked(run_at_startup)

        # Show settings page, hide cards
        self.settings_page.show()
        self.scroll_area.hide()

    def _cancel_settings(self):
        """Cancel settings changes and return to cards view."""
        self.settings_page.hide()
        self.scroll_area.show()

    def _save_settings(self):
        """Save settings and return to cards view."""
        # Save auto-refresh settings
        if self.auto_refresh_enabled.isChecked():
            interval_seconds = self.refresh_interval_spin.value() * 60
            self.config_manager.config["auto_refresh_interval"] = interval_seconds
            self.refresh_timer.setInterval(interval_seconds * 1000)
            if not self.refresh_timer.isActive():
                self.refresh_timer.start()
        else:
            self.config_manager.config["auto_refresh_interval"] = 0
            self.refresh_timer.stop()

        # Save stay on top setting
        stay_on_top = self.stay_on_top_check.isChecked()
        self.config_manager.config["stay_on_top"] = stay_on_top
        self.config_manager.save_config()

        # Apply stay on top
        if stay_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()  # Required to apply window flag changes

        # Save and apply run at startup setting
        run_at_startup = self.run_at_startup_check.isChecked()
        self.config_manager.config["run_at_startup"] = run_at_startup
        self.config_manager.save_config()
        self._set_run_at_startup(run_at_startup)

        # Return to cards view
        self.settings_page.hide()
        self.scroll_area.show()

    def _set_run_at_startup(self, enable: bool):
        """Enable or disable running at system startup (macOS Launch Agent)."""
        if platform.system() != "Darwin":  # macOS only
            return

        try:
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(parents=True, exist_ok=True)

            # Use a unique identifier for the plist file
            plist_name = "com.checkclouddrives.plist"
            plist_path = launch_agents_dir / plist_name

            if enable:
                # Get the path to the run.sh script
                project_root = Path(__file__).parent.parent.parent.parent
                script_path = project_root / "run.sh"

                if script_path.exists():
                    # Use the run.sh script
                    script_path = script_path.resolve()
                    # Use bash to execute the script
                    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.checkclouddrives</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>WorkingDirectory</key>
    <string>{project_root}</string>
</dict>
</plist>
"""
                else:
                    # Fallback: use Python with module
                    python_path = Path(sys.executable).resolve()
                    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.checkclouddrives</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>-m</string>
        <string>check_cloud_drives.main</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>WorkingDirectory</key>
    <string>{project_root}</string>
</dict>
</plist>
"""
                with open(plist_path, "w") as f:
                    f.write(plist_content)

                # Load the launch agent
                subprocess.run(["launchctl", "load", str(plist_path)], check=False)
            else:
                # Unload and remove the launch agent
                if plist_path.exists():
                    subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
                    plist_path.unlink()
        except Exception as e:
            print(f"Error setting run at startup: {e}")
            QMessageBox.warning(
                self,
                "Startup Setting Error",
                f"Could not {'enable' if enable else 'disable'} run at startup:\n{e}",
            )

    def _restore_geometry(self):
        """Restore window geometry from config, or position on right side by default."""
        geometry = self.config_manager.get_window_geometry()
        if geometry:
            self.setGeometry(
                geometry.get("x", 100),
                geometry.get("y", 100),
                geometry.get("width", 450),
                geometry.get("height", 600),
            )
        else:
            # Default: position on right side of screen
            screen = QApplication.primaryScreen().geometry()
            window_width = 450
            window_height = 600
            x = screen.right() - window_width
            y = (screen.height() - window_height) // 2  # Center vertically
            self.setGeometry(x, y, window_width, window_height)

        if self.config_manager.get_stay_on_top():
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def _title_mouse_press(self, event):
        """Handle mouse press on title for window dragging."""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _title_mouse_move(self, event):
        """Handle mouse move on title for window dragging."""
        if self.is_dragging and event.buttons() == Qt.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            event.accept()

    def _title_mouse_release(self, event):
        """Handle mouse release on title and snap to screen edge if near."""
        if self.is_dragging:
            self.is_dragging = False
            self._snap_to_edge()
        event.accept()

    def _show_overlay(self):
        """Show the dimming overlay over the main window."""
        if hasattr(self, 'overlay'):
            central = self.centralWidget()
            if central:
                # Position overlay to cover entire central widget
                self.overlay.setGeometry(0, 0, central.width(), central.height())
                self.overlay.show()
                self.overlay.raise_()  # Bring to front

    def _hide_overlay(self):
        """Hide the dimming overlay."""
        if hasattr(self, 'overlay'):
            self.overlay.hide()

    def resizeEvent(self, event):
        """Handle window resize to update overlay size."""
        super().resizeEvent(event)
        if hasattr(self, 'overlay') and self.overlay.isVisible():
            central = self.centralWidget()
            if central:
                self.overlay.setGeometry(central.geometry())

    def _snap_to_edge(self):
        """Snap window to screen edge if close enough."""
        screen = QApplication.primaryScreen().geometry()
        window_geo = self.geometry()

        # Check left edge
        if abs(window_geo.left() - screen.left()) < self.edge_snap_threshold:
            self.move(screen.left(), window_geo.top())
        # Check right edge
        elif abs(window_geo.right() - screen.right()) < self.edge_snap_threshold:
            self.move(screen.right() - window_geo.width(), window_geo.top())
        # Check top edge
        elif abs(window_geo.top() - screen.top()) < self.edge_snap_threshold:
            self.move(window_geo.left(), screen.top())
        # Check bottom edge
        elif abs(window_geo.bottom() - screen.bottom()) < self.edge_snap_threshold:
            self.move(window_geo.left(), screen.bottom() - window_geo.height())

    def closeEvent(self, event):
        """Handle window close event."""
        # Save geometry
        geo = self.geometry()
        self.config_manager.set_window_geometry(
            {"x": geo.x(), "y": geo.y(), "width": geo.width(), "height": geo.height()}
        )

        # Hide instead of close if tray is available
        if QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
        else:
            event.accept()
