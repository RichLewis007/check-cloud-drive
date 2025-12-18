"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".toml", delete=False) as f:
        config_path = Path(f.name)
    yield config_path
    # Cleanup
    if config_path.exists():
        config_path.unlink()


@pytest.fixture
def sample_drive_config():
    """Create a sample DriveConfig for testing."""
    from check_cloud_drives.models import DriveConfig

    return DriveConfig(
        remote_name="test_remote",
        display_name="Test Drive",
        drive_type="googledrive",
        enabled=True,
    )


@pytest.fixture
def sample_drive_status():
    """Create a sample DriveStatus for testing."""
    from check_cloud_drives.models import DriveStatus

    return DriveStatus(
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
