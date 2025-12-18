"""Utility functions for UI components.

Author: Rich Lewis - @RichLewis007
"""

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


def get_assets_dir() -> Path:
    """Get the path to the assets directory."""
    # Get the project root (3 levels up from this file: ui -> check_cloud_drives -> src -> project_root)
    project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "assets"


def load_icon(drive_type: str, size: int = 56) -> tuple[QPixmap, float]:
    """Load icon for drive type, with fallback to placeholder."""
    # Try to load SVG icon from assets directory
    assets_dir = get_assets_dir()
    icon_path = assets_dir / "icons" / f"{drive_type}.svg"

    # Also check for common typos/variations
    if not icon_path.exists():
        if drive_type == "googledrive":
            # Check for googledrive icon
            alt_path = assets_dir / "icons" / "googledrive.svg"
            if alt_path.exists():
                icon_path = alt_path
        elif drive_type == "onedrive":
            # Ensure onedrive icon is used
            alt_path = assets_dir / "icons" / "onedrive.svg"
            if alt_path.exists():
                icon_path = alt_path

    if icon_path.exists():
        try:
            # Use QSvgRenderer directly for better control over viewBox rendering
            # QIcon can sometimes crop SVGs, so we'll use QSvgRenderer for more precise control

            # Use QSvgRenderer - render entire viewBox to full pixmap
            renderer = QSvgRenderer(str(icon_path))
            if renderer.isValid():
                # Get viewBox - this defines the coordinate system of the SVG
                view_box = renderer.viewBox()
                view_width = view_box.width()
                view_height = view_box.height()
                aspect_ratio = view_width / view_height if view_height > 0 else 1.0

                # Calculate dimensions maintaining aspect ratio
                # Use 'size' as the maximum dimension to prevent cards from becoming too wide
                if aspect_ratio >= 1.0:
                    # Wider than tall - limit width to size, calculate height
                    icon_width = size
                    icon_height = int(size / aspect_ratio)
                else:
                    # Taller than wide - use size as height, calculate width
                    icon_height = size
                    icon_width = int(size * aspect_ratio)

                # Create pixmap with the calculated dimensions
                image = QImage(icon_width, icon_height, QImage.Format_ARGB32)
                image.fill(0x00000000)  # Transparent background

                painter = QPainter(image)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)

                # Render the SVG to the image maintaining aspect ratio
                renderer.render(painter, QRect(0, 0, icon_width, icon_height))
                painter.end()

                # Convert to pixmap
                final_pixmap = QPixmap.fromImage(image)

                if not final_pixmap.isNull() and final_pixmap.width() > 0:
                    return final_pixmap, aspect_ratio
                else:
                    print(f"QSvgRenderer produced null/empty pixmap for: {icon_path}")
        except Exception as e:
            print(f"Error loading SVG icon from {icon_path}: {e}")
            import traceback

            traceback.print_exc()
            pass
    else:
        print(f"SVG icon file not found: {icon_path} (drive_type: {drive_type})")

    # Fallback: create placeholder icon (square)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Draw colored circle based on drive type
    colors = {
        "googledrive": QColor(66, 133, 244),
        "onedrive": QColor(0, 120, 212),
        "dropbox": QColor(0, 126, 229),
        "protondrive": QColor(255, 255, 255),
    }
    color = colors.get(drive_type, QColor(100, 100, 100))
    painter.setBrush(color)
    painter.setPen(Qt.NoPen)
    margin = 4
    painter.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)

    # Draw emoji/letter (white text for contrast on colored background)
    painter.setPen(QColor(255, 255, 255))
    font_size = int(size * 0.5)
    painter.setFont(QFont("Arial", font_size, QFont.Bold))
    letter = drive_type[0].upper() if drive_type != "unknown" else "?"
    painter.drawText(pixmap.rect(), Qt.AlignCenter, letter)
    painter.end()

    return pixmap, 1.0  # Square aspect ratio for placeholder
