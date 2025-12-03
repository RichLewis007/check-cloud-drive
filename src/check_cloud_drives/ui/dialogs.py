"""Dialog components for the application."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from ..models import DriveConfig


class SetupDialog(QDialog):
    """Dialog for initial setup and adding drives."""

    def __init__(
        self, available_remotes: list[str], existing_drives: list[DriveConfig], parent=None
    ):
        super().__init__(parent)
        self.available_remotes = available_remotes
        self.existing_remotes = {d.remote_name for d in existing_drives}
        self.selected_drives: list[DriveConfig] = []
        self.setWindowTitle("Setup Cloud Drives")
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the setup dialog UI."""
        # Apply font to dialog
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
        for remote in self.available_remotes:
            if remote not in self.existing_remotes:
                item = QListWidgetItem(remote)
                item.setCheckState(Qt.Unchecked)
                self.remotes_list.addItem(item)
        layout.addWidget(self.remotes_list)

        # Manual entry
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Or add manually:"))
        self.manual_remote = QLineEdit()
        self.manual_remote.setPlaceholderText("Enter rclone remote name")
        manual_layout.addWidget(self.manual_remote)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_manual)
        manual_layout.addWidget(add_btn)
        layout.addLayout(manual_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_manual(self):
        """Add manually entered remote."""
        remote_name = self.manual_remote.text().strip()
        if remote_name and remote_name not in self.existing_remotes:
            item = QListWidgetItem(remote_name)
            item.setCheckState(Qt.Checked)
            self.remotes_list.addItem(item)
            self.manual_remote.clear()
            self.existing_remotes.add(remote_name)

    def _accept(self):
        """Collect selected drives and accept."""
        for i in range(self.remotes_list.count()):
            item = self.remotes_list.item(i)
            if item.checkState() == Qt.Checked:
                remote_name = item.text()
                display_name = self._guess_display_name(remote_name)
                drive_type = self._guess_drive_type(remote_name)
                self.selected_drives.append(
                    DriveConfig(
                        remote_name=remote_name, display_name=display_name, drive_type=drive_type
                    )
                )
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
