"""Main entry point for the application."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .fonts import setup_bundled_fonts
from .ui.window import MainWindow


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Load bundled fonts before creating UI
    # Determine project root (go up from src/check_cloud_drives/main.py)
    project_root = Path(__file__).parent.parent.parent
    setup_bundled_fonts(project_root)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
