"""Utility functions for UI components."""

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


def get_assets_dir() -> Path:
    """Get the path to the assets directory."""
    # Get the project root (3 levels up from this file: ui -> check_cloud_drives -> src -> project_root)
    project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "assets"


def load_icon(drive_type: str, size: int = 56) -> QPixmap:
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

                # Create pixmap with some extra space to ensure nothing is cropped
                # Add 15% padding to account for viewBox bounds
                padded_size = int(size * 1.15)

                image = QImage(padded_size, padded_size, QImage.Format_ARGB32)
                image.fill(0x00000000)  # Transparent background

                painter = QPainter(image)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)

                # Simply render the SVG to the full image - QSvgRenderer handles viewBox automatically
                # The renderer will scale the viewBox to fit the target rectangle
                # Using the full padded size ensures the entire viewBox is visible
                renderer.render(painter, QRect(0, 0, padded_size, padded_size))
                painter.end()

                # Convert to pixmap and scale down to desired size, maintaining aspect ratio
                pixmap = QPixmap.fromImage(image)
                final_pixmap = pixmap.scaled(
                    size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )

                if not final_pixmap.isNull() and final_pixmap.width() > 0:
                    print(
                        f"Successfully loaded SVG icon: {icon_path} (viewBox: {view_box}, size: {size})"
                    )
                    return final_pixmap
                else:
                    print(f"QSvgRenderer produced null/empty pixmap for: {icon_path}")
        except Exception as e:
            print(f"Error loading SVG icon from {icon_path}: {e}")
            import traceback

            traceback.print_exc()
            pass
    else:
        print(f"SVG icon file not found: {icon_path} (drive_type: {drive_type})")

    # Fallback: create placeholder icon
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

    return pixmap
