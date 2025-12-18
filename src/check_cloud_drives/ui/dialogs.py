"""Dialog components for the application.

Author: Rich Lewis - @RichLewis007
"""

import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ..models import DriveConfig


class SetupDialog(QDialog):
    """Dialog for initial setup and adding drives."""

    def __init__(
        self,
        available_remotes: list[str],
        existing_drives: list[DriveConfig],
        drive_order: list[str] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.available_remotes = available_remotes
        self.existing_drives = existing_drives
        self.existing_remotes = {d.remote_name for d in existing_drives}
        self.drive_order = drive_order or []
        self.selected_drives: list[DriveConfig] = []
        self.removed_drives: list[str] = []  # Remotes that were unchecked
        self.setWindowTitle("Setup Cloud Drives")
        self.setWindowModality(Qt.ApplicationModal)  # Program modal - blocks entire application
        # Set minimum size to make dialog taller
        self.setMinimumSize(500, 600)
        self.resize(500, 600)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the setup dialog UI."""
        # Apply font to dialog
        from PySide6.QtGui import QFont

        app_font = QFont("AtkynsonMono Nerd Font Propo", -1)
        self.setFont(app_font)

        self.setStyleSheet("""
            QDialog {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
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
            QListWidget::item {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
            QPushButton {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
            }
        """)

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Select the cloud drives you want to monitor, or add a new one manually."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Available remotes list
        list_label = QLabel("Available Rclone Remotes:")
        layout.addWidget(list_label)

        self.remotes_list = QListWidget()
        app_font = QFont("AtkynsonMono Nerd Font Propo", 13)

        # Create a dict for quick lookup of existing drives
        existing_dict = {d.remote_name: d for d in self.existing_drives}

        # First, add existing drives in their saved order
        for remote_name in self.drive_order:
            if remote_name in existing_dict:
                item = QListWidgetItem(remote_name)
                item.setFont(app_font)
                item.setCheckState(Qt.Checked)  # Existing drives are checked
                self.remotes_list.addItem(item)

        # Then add any other existing drives not in the order
        for drive in self.existing_drives:
            if drive.remote_name not in self.drive_order:
                item = QListWidgetItem(drive.remote_name)
                item.setFont(app_font)
                item.setCheckState(Qt.Checked)  # Existing drives are checked
                self.remotes_list.addItem(item)

        # Finally, add new remotes that aren't already added
        for remote in self.available_remotes:
            if remote not in self.existing_remotes:
                item = QListWidgetItem(remote)
                item.setFont(app_font)
                item.setCheckState(Qt.Unchecked)  # New remotes start unchecked
                self.remotes_list.addItem(item)

        layout.addWidget(self.remotes_list)

        # Set minimum height for the list widget to make it taller
        self.remotes_list.setMinimumHeight(300)

        # Standard button styling (font, size, padding) - define early for reuse
        standard_button_style = """
            QPushButton {
                font-family: "AtkynsonMono Nerd Font Propo", monospace;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
        """

        # Create a reference button to get standard height
        ref_button = QPushButton("Cancel")
        ref_button.setStyleSheet(standard_button_style)
        standard_button_height = ref_button.sizeHint().height()
        ref_button.deleteLater()

        # Manual entry
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Add manually:"))
        self.manual_remote = QLineEdit()
        self.manual_remote.setPlaceholderText("Enter rclone remote name")
        manual_layout.addWidget(self.manual_remote)
        add_btn = QPushButton("Add")
        add_btn.setFixedHeight(standard_button_height)
        add_btn.setStyleSheet(
            standard_button_style
            + """
            QPushButton {
                color: #ffffff;
                background-color: #3498db;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        )
        add_btn.clicked.connect(self._add_manual)
        manual_layout.addWidget(add_btn)
        layout.addLayout(manual_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        # Style both buttons with consistent font and get standard height
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)

        if cancel_button:
            # Style Cancel button with standard font
            cancel_button.setStyleSheet(
                standard_button_style
                + """
                QPushButton {
                    color: #2c3e50;
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                }
                QPushButton:hover {
                    background-color: #d5dbdb;
                }
                QPushButton:pressed {
                    background-color: #bfc9ca;
                }
            """
            )

        if ok_button:
            # Match Cancel button height and style OK button green
            ok_button.setFixedHeight(standard_button_height)
            ok_button.setStyleSheet(
                standard_button_style
                + """
                QPushButton {
                    color: #ffffff;
                    background-color: #27ae60;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """
            )

        layout.addWidget(buttons)

    def _show_centered_message(self, title: str, message: str, icon=QMessageBox.Warning):
        """Show a message box centered over this dialog."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(QMessageBox.Ok)

        # Center over parent dialog
        dialog_geometry = self.geometry()
        msg_box.adjustSize()
        msg_box.move(
            dialog_geometry.center().x() - msg_box.width() // 2,
            dialog_geometry.center().y() - msg_box.height() // 2,
        )

        msg_box.exec()

    def _normalize_remote_name(self, remote_name: str) -> str:
        """Normalize remote name by removing trailing colon if present.

        Rclone remote names can be entered with or without a trailing colon.
        This function ensures consistent storage without the colon.
        """
        if not remote_name:
            return remote_name
        return remote_name.strip().rstrip(":")

    def _add_manual(self):
        """Add manually entered remote."""
        from PySide6.QtGui import QFont

        remote_name = self._normalize_remote_name(self.manual_remote.text())
        if remote_name:
            # Check if it already exists in the list (compare normalized names)
            for i in range(self.remotes_list.count()):
                item = self.remotes_list.item(i)
                # Normalize the existing item's text for comparison
                existing_name = self._normalize_remote_name(item.text())
                if existing_name == remote_name:
                    # Already exists, just check it
                    item.setCheckState(Qt.Checked)
                    self.manual_remote.clear()
                    return

            # Validate remote by running rclone about command
            # Ensure remote name ends with colon for rclone command
            remote_with_colon = remote_name if remote_name.endswith(":") else remote_name + ":"

            try:
                result = subprocess.run(
                    ["rclone", "about", remote_with_colon],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode != 0:
                    # Remote is not set up in rclone
                    self._show_centered_message(
                        "Remote Not Found",
                        f"The remote '{remote_name}' has not been set up in rclone.\n\n"
                        f"Please configure this remote using 'rclone config' before adding it.",
                    )
                    return  # Don't add the remote, return to dialog

            except subprocess.TimeoutExpired:
                self._show_centered_message(
                    "Validation Timeout",
                    f"Timeout while validating remote '{remote_name}'.\n\n"
                    f"Please check your rclone configuration and try again.",
                )
                return
            except FileNotFoundError:
                self._show_centered_message(
                    "rclone Not Found",
                    "rclone is not installed or not in PATH.\n\n"
                    "Please install rclone from https://rclone.org/install/",
                )
                return
            except Exception as e:
                self._show_centered_message(
                    "Validation Error",
                    f"Error validating remote '{remote_name}': {str(e)}",
                )
                return

            # Validation passed - add new item with normalized name
            item = QListWidgetItem(remote_name)
            app_font = QFont("AtkynsonMono Nerd Font Propo", 13)
            item.setFont(app_font)
            item.setCheckState(Qt.Checked)
            self.remotes_list.addItem(item)
            self.manual_remote.clear()
            if remote_name not in self.existing_remotes:
                self.existing_remotes.add(remote_name)

    def _accept(self):
        """Collect selected drives and accept."""
        # Create dict of existing drives for lookup
        existing_dict = {d.remote_name: d for d in self.existing_drives}

        for i in range(self.remotes_list.count()):
            item = self.remotes_list.item(i)
            # Normalize remote name to ensure consistency (remove trailing colon if present)
            remote_name = self._normalize_remote_name(item.text())

            if item.checkState() == Qt.Checked:
                # Drive is checked - add to selected
                if remote_name in existing_dict:
                    # Use existing drive config
                    self.selected_drives.append(existing_dict[remote_name])
                else:
                    # New drive - create new config
                    display_name = self._guess_display_name(remote_name)
                    drive_type = self._guess_drive_type(remote_name)
                    self.selected_drives.append(
                        DriveConfig(
                            remote_name=remote_name,
                            display_name=display_name,
                            drive_type=drive_type,
                        )
                    )
            else:
                # Drive is unchecked - mark for removal if it was previously added
                if remote_name in self.existing_remotes:
                    self.removed_drives.append(remote_name)

        super().accept()

    def _guess_display_name(self, remote_name: str) -> str:
        """Guess a display name from remote name."""
        # Remove common suffixes
        name = remote_name.replace("-onedrive", "").replace("-gdrive", "")
        name = name.replace("-drive", "").replace(":", "")
        # Capitalize
        return name.replace("-", " ").title()

    def _guess_drive_type(self, remote_name: str) -> str:
        """Guess drive type from remote name."""
        remote_lower = remote_name.lower()
        if "gdrive" in remote_lower or "googledrive" in remote_lower:
            return "googledrive"
        elif "onedrive" in remote_lower:
            return "onedrive"
        elif "dropbox" in remote_lower:
            return "dropbox"
        elif "protondrive" in remote_lower:
            return "protondrive"
        else:
            return "unknown"
