"""Tests for ConfigManager."""

from check_cloud_drives.config import ConfigManager
from check_cloud_drives.models import DriveConfig


class TestConfigManager:
    """Test suite for ConfigManager."""

    def test_init_with_nonexistent_file(self, temp_config_file):
        """Test ConfigManager initialization with non-existent file creates default config."""
        # Remove the file if it exists
        if temp_config_file.exists():
            temp_config_file.unlink()

        manager = ConfigManager(temp_config_file)
        assert manager.config == {
            "drives": [],
            "window_geometry": {},
            "stay_on_top": False,
            "auto_refresh_interval": 300,
            "drive_order": [],
            "run_at_startup": False,
        }

    def test_init_with_existing_file(self, temp_config_file):
        """Test ConfigManager initialization with existing file loads config."""
        # Write a test config file
        config_content = b"""\
drives = [
    {remote_name = "test1", display_name = "Test 1", drive_type = "googledrive", enabled = true}
]
stay_on_top = true
auto_refresh_interval = 600
"""
        temp_config_file = temp_config_file.parent / "existing.toml"
        temp_config_file.write_bytes(config_content)

        manager = ConfigManager(temp_config_file)
        assert len(manager.get_drives()) == 1
        assert manager.get_stay_on_top() is True
        assert manager.config.get("auto_refresh_interval") == 600

    def test_init_with_invalid_file(self, temp_config_file):
        """Test ConfigManager initialization with invalid file falls back to defaults."""
        # Write invalid TOML
        temp_config_file.write_bytes(b"invalid toml content {[}")

        manager = ConfigManager(temp_config_file)
        # Should fall back to default config
        assert manager.config.get("drives") == []

    def test_get_drives_empty(self, temp_config_file):
        """Test getting drives from empty config."""
        manager = ConfigManager(temp_config_file)
        drives = manager.get_drives()
        assert drives == []

    def test_get_drives_with_data(self, temp_config_file):
        """Test getting drives from config with data."""
        manager = ConfigManager(temp_config_file)
        drive1 = DriveConfig("remote1", "Drive 1", "googledrive", True)
        drive2 = DriveConfig("remote2", "Drive 2", "onedrive", True)
        manager.set_drives([drive1, drive2])

        drives = manager.get_drives()
        assert len(drives) == 2
        assert drives[0].remote_name == "remote1"
        assert drives[1].remote_name == "remote2"

    def test_set_drives(self, temp_config_file):
        """Test setting drives saves to config."""
        manager = ConfigManager(temp_config_file)
        drive = DriveConfig("test_remote", "Test Drive", "googledrive", True)
        manager.set_drives([drive])

        # Verify it was saved
        assert len(manager.get_drives()) == 1
        assert manager.get_drives()[0].remote_name == "test_remote"
        # Verify file was written
        assert temp_config_file.exists()

    def test_get_drive_order_empty(self, temp_config_file):
        """Test getting drive order from empty config."""
        manager = ConfigManager(temp_config_file)
        order = manager.get_drive_order()
        assert order == []

    def test_set_drive_order(self, temp_config_file):
        """Test setting drive order saves to config."""
        manager = ConfigManager(temp_config_file)
        order = ["remote1", "remote2", "remote3"]
        manager.set_drive_order(order)

        assert manager.get_drive_order() == order
        assert temp_config_file.exists()

    def test_get_window_geometry_none(self, temp_config_file):
        """Test getting window geometry when not set."""
        manager = ConfigManager(temp_config_file)
        geometry = manager.get_window_geometry()
        assert geometry is None

    def test_set_window_geometry(self, temp_config_file):
        """Test setting window geometry saves to config."""
        manager = ConfigManager(temp_config_file)
        geometry = {"x": 100, "y": 200, "width": 800, "height": 600}
        manager.set_window_geometry(geometry)

        assert manager.get_window_geometry() == geometry

    def test_set_window_geometry_none(self, temp_config_file):
        """Test setting window geometry to None converts to empty dict."""
        manager = ConfigManager(temp_config_file)
        manager.set_window_geometry(None)

        geometry = manager.get_window_geometry()
        assert geometry is None

    def test_get_stay_on_top_default(self, temp_config_file):
        """Test getting stay_on_top default value."""
        manager = ConfigManager(temp_config_file)
        assert manager.get_stay_on_top() is False

    def test_set_stay_on_top(self, temp_config_file):
        """Test setting stay_on_top saves to config."""
        manager = ConfigManager(temp_config_file)
        manager.set_stay_on_top(True)

        assert manager.get_stay_on_top() is True
        assert manager.config.get("stay_on_top") is True

    def test_save_config_creates_directory(self, temp_config_file):
        """Test that save_config creates parent directory if it doesn't exist."""
        # Use a path in a non-existent directory
        deep_path = temp_config_file.parent / "deep" / "path" / "config.toml"
        manager = ConfigManager(deep_path)
        manager.set_stay_on_top(True)

        assert deep_path.exists()
        assert deep_path.parent.exists()

    def test_prepare_for_toml_handles_none(self, temp_config_file):
        """Test _prepare_for_toml handles None values correctly."""
        manager = ConfigManager(temp_config_file)
        manager.config["test_none"] = None
        manager.config["window_geometry"] = None

        prepared = manager._prepare_for_toml(manager.config)
        assert "test_none" not in prepared
        assert prepared["window_geometry"] == {}

    def test_prepare_for_toml_handles_empty_dict(self, temp_config_file):
        """Test _prepare_for_toml handles empty dicts correctly."""
        manager = ConfigManager(temp_config_file)
        manager.config["empty_dict"] = {}
        manager.config["window_geometry"] = {}

        prepared = manager._prepare_for_toml(manager.config)
        # window_geometry should be included even if empty
        assert "window_geometry" in prepared
        # Other empty dicts should be excluded
        assert "empty_dict" not in prepared

    def test_config_persistence(self, temp_config_file):
        """Test that config persists across ConfigManager instances."""
        # Create first manager and set some values
        manager1 = ConfigManager(temp_config_file)
        drive = DriveConfig("persistent_remote", "Persistent Drive", "googledrive", True)
        manager1.set_drives([drive])
        manager1.set_stay_on_top(True)
        manager1.set_drive_order(["persistent_remote"])

        # Create second manager with same file
        manager2 = ConfigManager(temp_config_file)
        assert len(manager2.get_drives()) == 1
        assert manager2.get_drives()[0].remote_name == "persistent_remote"
        assert manager2.get_stay_on_top() is True
        assert manager2.get_drive_order() == ["persistent_remote"]
