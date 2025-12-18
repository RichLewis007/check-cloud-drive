# Tests

**Author:** Rich Lewis - @RichLewis007

This directory contains unit tests for the check-cloud-drives application.

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with verbose output:
```bash
pytest -v
```

### Run specific test file:
```bash
pytest tests/test_config.py
```

### Run specific test:
```bash
pytest tests/test_config.py::TestConfigManager::test_get_drives_empty
```

### Run with coverage:
```bash
pytest --cov=check_cloud_drives --cov-report=html
```

### Run only fast tests (exclude slow tests):
```bash
pytest -m "not slow"
```

## Test Structure

- `test_config.py` - Tests for `ConfigManager` (config loading/saving)
- `test_models.py` - Tests for data models (`DriveConfig`, `DriveStatus`)
- `test_rclone.py` - Tests for rclone integration (status fetching)
- `test_card.py` - Tests for `DriveCard` UI component (edit mode, display)

## Fixtures

Shared test fixtures are defined in `conftest.py`:
- `temp_config_file` - Temporary config file for testing
- `sample_drive_config` - Sample `DriveConfig` instance
- `sample_drive_status` - Sample `DriveStatus` instance
- `qapp` - QApplication instance for Qt tests
- `drive_card` - `DriveCard` instance for testing

## Requirements

Tests require:
- `pytest>=8.0.0`
- `pytest-qt>=4.2.0` (for Qt widget tests)
- `pytest-mock>=3.12.0` (for mocking)

Install with:
```bash
uv sync
```

