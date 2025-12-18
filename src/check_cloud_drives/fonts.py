"""Font loading utilities for bundled fonts.

Author: Rich Lewis - @RichLewis007
"""

import atexit
import zipfile
from pathlib import Path

from PySide6.QtGui import QFontDatabase

# Store extracted font file paths to keep them alive for the application lifetime
_extracted_font_files: list[Path] = []


def _cleanup_font_files():
    """Clean up extracted font files on application exit."""
    for font_path in _extracted_font_files:
        try:
            if font_path.exists():
                font_path.unlink()
        except Exception:
            pass  # Ignore errors during cleanup


# Register cleanup function to run on exit
atexit.register(_cleanup_font_files)


def load_font_from_zip(zip_path: Path, font_name_in_zip: str) -> bool:
    """
    Load a font file from a zip archive into Qt's font database.

    Args:
        zip_path: Path to the zip file containing fonts
        font_name_in_zip: Name of the font file inside the zip (e.g., "AtkynsonMonoNerdFontPropo-Regular.otf")

    Returns:
        True if font was loaded successfully, False otherwise
    """
    if not zip_path.exists():
        print(f"Font zip file not found: {zip_path}")
        return False

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Check if font file exists in zip
            if font_name_in_zip not in zip_ref.namelist():
                print(f"Font file '{font_name_in_zip}' not found in zip: {zip_path}")
                return False

            # Extract font to a persistent cache directory
            # Qt requires the font file to remain accessible for the lifetime of the application
            import os

            # Use platform-appropriate cache directory
            if os.name == "nt":  # Windows
                cache_base = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")))
            else:  # Unix-like (macOS, Linux)
                cache_base = Path(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")))

            cache_dir = cache_base / "check-cloud-drives" / "fonts"
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Use a stable filename based on the font name
            font_cache_path = cache_dir / font_name_in_zip

            # Only extract if not already cached
            if not font_cache_path.exists():
                with open(font_cache_path, "wb") as f:
                    f.write(zip_ref.read(font_name_in_zip))

            # Store path to keep file alive for application lifetime
            _extracted_font_files.append(font_cache_path)

            # Load font into Qt's font database
            font_id = QFontDatabase.addApplicationFont(str(font_cache_path))
            if font_id == -1:
                print(f"Failed to load font: {font_name_in_zip}")
                return False

            # Verify font was loaded by checking font families
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                # Successfully loaded - don't print success message
                return True
            else:
                print(f"Font loaded but no families found: {font_name_in_zip}")
                return False

    except Exception as e:
        print(f"Error loading font from zip: {e}")
        import traceback

        traceback.print_exc()
        return False


def load_all_fonts_from_zip(zip_path: Path, font_pattern: str = "Propo") -> int:
    """
    Load all matching font files from a zip archive.

    Args:
        zip_path: Path to the zip file containing fonts
        font_pattern: Pattern to match font files (default: "Propo" for proportional fonts)

    Returns:
        Number of fonts successfully loaded
    """
    if not zip_path.exists():
        print(f"Font zip file not found: {zip_path}")
        return 0

    loaded_count = 0
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Find all font files matching the pattern
            font_files = [f for f in zip_ref.namelist() if font_pattern in f and f.endswith(".otf")]

            for font_file in font_files:
                if load_font_from_zip(zip_path, font_file):
                    loaded_count += 1

        # Don't print success message - only show errors
        return loaded_count

    except Exception as e:
        print(f"Error loading fonts from zip: {e}")
        import traceback

        traceback.print_exc()
        return 0


def _find_font_zip() -> Path | None:
    """
    Find the font zip file in multiple possible locations.

    Checks:
    1. Development location: project_root/assets/fonts/
    2. Installed package location: using importlib.resources
    3. System data directory (for hatchling shared-data)

    Returns:
        Path to font zip file if found, None otherwise
    """
    font_zip_name = "AtkinsonHyperlegibleMono.zip"

    # Try 1: Development location (relative to source file)
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    dev_font_zip = project_root / "assets" / "fonts" / font_zip_name
    if dev_font_zip.exists():
        return dev_font_zip

    # Try 2: Installed package location using importlib.resources
    try:
        import importlib.resources

        # For hatchling shared-data, assets are installed alongside the package
        # Try to find the package location and look for assets nearby
        try:
            # Python 3.9+ approach
            package_files = importlib.resources.files("check_cloud_drives")
            package_path = Path(str(package_files))
        except (AttributeError, TypeError):
            # Fallback for older Python or different structure
            import check_cloud_drives

            package_path = Path(check_cloud_drives.__file__).parent

        # Hatchling shared-data installs assets at the same level as site-packages
        # Check multiple possible locations
        search_paths = [
            package_path.parent / "assets" / "fonts" / font_zip_name,  # Same level as package
            package_path.parent.parent / "assets" / "fonts" / font_zip_name,  # One level up
            package_path
            / "assets"
            / "fonts"
            / font_zip_name,  # Inside package (unlikely but possible)
        ]

        for search_path in search_paths:
            if search_path.exists():
                return search_path
    except Exception:
        # Silently continue to next search method
        pass

    # Try 3: Check common system data directories
    import sys

    if hasattr(sys, "prefix"):
        # Check site-packages/assets (where shared-data might install)
        for site_packages in [
            Path(sys.prefix)
            / "lib"
            / f"python{sys.version_info.major}.{sys.version_info.minor}"
            / "site-packages",
            Path(sys.prefix) / "Lib" / "site-packages",
        ]:  # Windows
            if site_packages.exists():
                system_font_zip = site_packages / "assets" / "fonts" / font_zip_name
                if system_font_zip.exists():
                    return system_font_zip

    return None


def setup_bundled_fonts(project_root: Path | None = None) -> bool:
    """
    Set up bundled fonts for the application.

    This function looks for the font zip file in multiple locations
    (development and installed package) and loads the required fonts
    into Qt's font database.

    Args:
        project_root: Root directory of the project (for development).
                     If None, attempts to find it automatically.
                     This parameter is kept for backward compatibility
                     but the function now searches multiple locations.

    Returns:
        True if at least one font was loaded successfully, False otherwise
    """
    # Find font zip file in any available location
    font_zip = _find_font_zip()

    if font_zip is None or not font_zip.exists():
        print("Font zip file not found in any standard location.")
        print("Application will use system fonts if available.")
        return False

    # Load the proportional font variant (used throughout the app)
    # The app uses "AtkynsonMono Nerd Font Propo" which corresponds to
    # "AtkynsonMonoNerdFontPropo-Regular.otf" in the zip
    success = load_font_from_zip(font_zip, "AtkynsonMonoNerdFontPropo-Regular.otf")

    # Optionally load other variants for better font rendering
    if success:
        # Load other Propo variants for different weights/styles
        load_font_from_zip(font_zip, "AtkynsonMonoNerdFontPropo-Bold.otf")
        load_font_from_zip(font_zip, "AtkynsonMonoNerdFontPropo-Italic.otf")
        load_font_from_zip(font_zip, "AtkynsonMonoNerdFontPropo-BoldItalic.otf")
        load_font_from_zip(font_zip, "AtkynsonMonoNerdFontPropo-Medium.otf")

    return success
