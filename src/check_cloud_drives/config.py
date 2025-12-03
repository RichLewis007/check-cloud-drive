"""Configuration management for the application."""

from pathlib import Path

import tomli_w

# Use built-in tomllib for Python 3.11+, fallback to tomli for older versions
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older Python versions

from .models import DriveConfig


class ConfigManager:
    """Manages configuration file for drive settings."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from TOML file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "rb") as f:
                    return tomllib.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "drives": [],
            "window_geometry": {},
            "stay_on_top": False,
            "auto_refresh_interval": 300,  # seconds
            "drive_order": [],
            "run_at_startup": False,
        }

    def _prepare_for_toml(self, data: dict) -> dict:
        """Prepare config data for TOML serialization (handle None values and empty dicts)."""
        result = {}
        for key, value in data.items():
            if value is None:
                # Skip None values in TOML (or convert to empty dict for window_geometry)
                if key == "window_geometry":
                    result[key] = {}
                # Otherwise skip the key
            elif isinstance(value, dict):
                prepared = self._prepare_for_toml(value)
                # Only include non-empty dicts (unless it's window_geometry which we always include)
                if prepared or key == "window_geometry":
                    result[key] = prepared
            elif isinstance(value, list):
                result[key] = [
                    self._prepare_for_toml(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def save_config(self):
        """Save configuration to TOML file."""
        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            # Prepare config for TOML (handle None values)
            toml_data = self._prepare_for_toml(self.config)
            with open(self.config_path, "wb") as f:
                tomli_w.dump(toml_data, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_drives(self) -> list[DriveConfig]:
        """Get list of configured drives."""
        return [DriveConfig.from_dict(d) for d in self.config.get("drives", [])]

    def set_drives(self, drives: list[DriveConfig]):
        """Set list of configured drives."""
        self.config["drives"] = [d.to_dict() for d in drives]
        self.save_config()

    def get_drive_order(self) -> list[str]:
        """Get the order of drive remote names."""
        return self.config.get("drive_order", [])

    def set_drive_order(self, order: list[str]):
        """Set the order of drive remote names."""
        self.config["drive_order"] = order
        self.save_config()

    def get_window_geometry(self) -> dict | None:
        """Get saved window geometry."""
        geometry = self.config.get("window_geometry")
        # Handle empty dict as None
        if isinstance(geometry, dict) and not geometry:
            return None
        return geometry

    def set_window_geometry(self, geometry: dict):
        """Save window geometry."""
        # Convert None to empty dict for TOML compatibility
        self.config["window_geometry"] = geometry if geometry else {}
        self.save_config()

    def get_stay_on_top(self) -> bool:
        """Get stay on top setting."""
        return self.config.get("stay_on_top", False)

    def set_stay_on_top(self, value: bool):
        """Set stay on top setting."""
        self.config["stay_on_top"] = value
        self.save_config()
