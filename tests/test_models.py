"""Tests for data models (DriveConfig and DriveStatus)."""

from check_cloud_drives.models import DriveConfig, DriveStatus


class TestDriveConfig:
    """Test suite for DriveConfig model."""

    def test_create_drive_config(self):
        """Test creating a DriveConfig with required fields."""
        config = DriveConfig(
            remote_name="test_remote",
            display_name="Test Drive",
        )
        assert config.remote_name == "test_remote"
        assert config.display_name == "Test Drive"
        assert config.drive_type == "unknown"  # Default value
        assert config.enabled is True  # Default value

    def test_create_drive_config_with_all_fields(self):
        """Test creating a DriveConfig with all fields."""
        config = DriveConfig(
            remote_name="test_remote",
            display_name="Test Drive",
            drive_type="googledrive",
            enabled=False,
        )
        assert config.remote_name == "test_remote"
        assert config.display_name == "Test Drive"
        assert config.drive_type == "googledrive"
        assert config.enabled is False

    def test_drive_config_to_dict(self):
        """Test converting DriveConfig to dictionary."""
        config = DriveConfig(
            remote_name="test_remote",
            display_name="Test Drive",
            drive_type="onedrive",
            enabled=True,
        )
        data = config.to_dict()
        assert data == {
            "remote_name": "test_remote",
            "display_name": "Test Drive",
            "drive_type": "onedrive",
            "enabled": True,
        }

    def test_drive_config_from_dict(self):
        """Test creating DriveConfig from dictionary."""
        data = {
            "remote_name": "test_remote",
            "display_name": "Test Drive",
            "drive_type": "dropbox",
            "enabled": False,
        }
        config = DriveConfig.from_dict(data)
        assert config.remote_name == "test_remote"
        assert config.display_name == "Test Drive"
        assert config.drive_type == "dropbox"
        assert config.enabled is False

    def test_drive_config_from_dict_with_defaults(self):
        """Test creating DriveConfig from dictionary with missing optional fields."""
        data = {
            "remote_name": "test_remote",
            "display_name": "Test Drive",
        }
        config = DriveConfig.from_dict(data)
        assert config.remote_name == "test_remote"
        assert config.display_name == "Test Drive"
        assert config.drive_type == "unknown"  # Default
        assert config.enabled is True  # Default

    def test_drive_config_round_trip(self):
        """Test converting DriveConfig to dict and back."""
        original = DriveConfig(
            remote_name="test_remote",
            display_name="Test Drive",
            drive_type="googledrive",
            enabled=True,
        )
        data = original.to_dict()
        restored = DriveConfig.from_dict(data)
        assert restored.remote_name == original.remote_name
        assert restored.display_name == original.display_name
        assert restored.drive_type == original.drive_type
        assert restored.enabled == original.enabled


class TestDriveStatus:
    """Test suite for DriveStatus model."""

    def test_create_drive_status_minimal(self):
        """Test creating a DriveStatus with minimal fields."""
        status = DriveStatus(remote_name="test_remote")
        assert status.remote_name == "test_remote"
        assert status.total == "Unknown"  # Default
        assert status.used == "Unknown"  # Default
        assert status.free == "Unknown"  # Default
        assert status.trash == "Unknown"  # Default
        assert status.other == "Unknown"  # Default
        assert status.objects == "Unknown"  # Default
        assert status.last_updated == "Never"  # Default
        assert status.error is None  # Default

    def test_create_drive_status_with_all_fields(self):
        """Test creating a DriveStatus with all fields."""
        status = DriveStatus(
            remote_name="test_remote",
            total="100 GB",
            used="50 GB",
            free="50 GB",
            trash="1 GB",
            other="0 GB",
            objects="1000",
            last_updated="2024-01-15 14:30:00",
            error=None,
        )
        assert status.remote_name == "test_remote"
        assert status.total == "100 GB"
        assert status.used == "50 GB"
        assert status.free == "50 GB"
        assert status.trash == "1 GB"
        assert status.other == "0 GB"
        assert status.objects == "1000"
        assert status.last_updated == "2024-01-15 14:30:00"
        assert status.error is None

    def test_create_drive_status_with_error(self):
        """Test creating a DriveStatus with an error."""
        status = DriveStatus(
            remote_name="test_remote",
            error="Connection failed",
        )
        assert status.remote_name == "test_remote"
        assert status.error == "Connection failed"

    def test_drive_status_to_dict(self):
        """Test converting DriveStatus to dictionary."""
        status = DriveStatus(
            remote_name="test_remote",
            total="100 GB",
            used="50 GB",
            free="50 GB",
            error="Test error",
        )
        data = status.to_dict()
        assert data == {
            "remote_name": "test_remote",
            "total": "100 GB",
            "used": "50 GB",
            "free": "50 GB",
            "trash": "Unknown",
            "other": "Unknown",
            "objects": "Unknown",
            "last_updated": "Never",
            "error": "Test error",
        }

    def test_drive_status_from_dict(self):
        """Test creating DriveStatus from dictionary."""
        data = {
            "remote_name": "test_remote",
            "total": "200 GB",
            "used": "100 GB",
            "free": "100 GB",
            "trash": "2 GB",
            "other": "1 GB",
            "objects": "2000",
            "last_updated": "2024-01-16 10:00:00",
            "error": None,
        }
        status = DriveStatus.from_dict(data)
        assert status.remote_name == "test_remote"
        assert status.total == "200 GB"
        assert status.used == "100 GB"
        assert status.free == "100 GB"
        assert status.trash == "2 GB"
        assert status.other == "1 GB"
        assert status.objects == "2000"
        assert status.last_updated == "2024-01-16 10:00:00"
        assert status.error is None

    def test_drive_status_from_dict_with_defaults(self):
        """Test creating DriveStatus from dictionary with missing optional fields."""
        data = {
            "remote_name": "test_remote",
        }
        status = DriveStatus.from_dict(data)
        assert status.remote_name == "test_remote"
        assert status.total == "Unknown"
        assert status.used == "Unknown"
        assert status.free == "Unknown"
        assert status.error is None

    def test_drive_status_round_trip(self):
        """Test converting DriveStatus to dict and back."""
        original = DriveStatus(
            remote_name="test_remote",
            total="100 GB",
            used="50 GB",
            free="50 GB",
            trash="1 GB",
            other="0 GB",
            objects="1000",
            last_updated="2024-01-15 14:30:00",
            error="Test error",
        )
        data = original.to_dict()
        restored = DriveStatus.from_dict(data)
        assert restored.remote_name == original.remote_name
        assert restored.total == original.total
        assert restored.used == original.used
        assert restored.free == original.free
        assert restored.trash == original.trash
        assert restored.other == original.other
        assert restored.objects == original.objects
        assert restored.last_updated == original.last_updated
        assert restored.error == original.error

    def test_drive_status_validation(self):
        """Test that DriveStatus accepts various string formats for sizes."""
        # Test with different size formats
        status1 = DriveStatus(remote_name="test1", total="100 GB", used="50 GB", free="50 GB")
        status2 = DriveStatus(remote_name="test2", total="1 TB", used="500 GB", free="500 GB")
        status3 = DriveStatus(remote_name="test3", total="50 MB", used="25 MB", free="25 MB")

        assert status1.total == "100 GB"
        assert status2.total == "1 TB"
        assert status3.total == "50 MB"
