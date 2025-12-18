"""Tests for rclone integration."""

import pytest

from check_cloud_drives.rclone import RcloneWorker


class TestRcloneWorker:
    """Test suite for RcloneWorker."""

    def test_parse_about_output_success(self):
        """Test parsing successful rclone about output."""
        output = """Total:   100 GB
Used:    50 GB
Free:    50 GB
Trash:   1 GB
Other:   0 GB
Objects: 1000
"""
        worker = RcloneWorker(["rclone", "about", "test:"], "test_remote")
        result = worker._parse_about_output(output)

        assert result["total"] == "100 GB"
        assert result["used"] == "50 GB"
        assert result["free"] == "50 GB"
        assert result["trash"] == "1 GB"
        assert result["other"] == "0 GB"
        assert result["objects"] == "1000"
        assert "raw" in result

    def test_parse_about_output_case_insensitive(self):
        """Test that parsing is case-insensitive."""
        output = """TOTAL:   200 GB
USED:    100 GB
FREE:    100 GB
"""
        worker = RcloneWorker(["rclone", "about", "test:"], "test_remote")
        result = worker._parse_about_output(output)

        assert result["total"] == "200 GB"
        assert result["used"] == "100 GB"
        assert result["free"] == "100 GB"

    def test_parse_about_output_missing_fields(self):
        """Test parsing output with missing fields."""
        output = """Total:   100 GB
Used:    50 GB
"""
        worker = RcloneWorker(["rclone", "about", "test:"], "test_remote")
        result = worker._parse_about_output(output)

        assert result["total"] == "100 GB"
        assert result["used"] == "50 GB"
        assert result["free"] == "Unknown"  # Missing field
        assert result["trash"] == "Unknown"
        assert result["other"] == "Unknown"
        assert result["objects"] == "Unknown"

    def test_parse_about_output_empty(self):
        """Test parsing empty output."""
        worker = RcloneWorker(["rclone", "about", "test:"], "test_remote")
        result = worker._parse_about_output("")

        assert result["total"] == "Unknown"
        assert result["used"] == "Unknown"
        assert result["free"] == "Unknown"
        assert result["trash"] == "Unknown"
        assert result["other"] == "Unknown"
        assert result["objects"] == "Unknown"

    def test_parse_about_output_malformed(self):
        """Test parsing malformed output."""
        output = """Some random text
Not in expected format
Total: 100 GB (but with extra text)
"""
        worker = RcloneWorker(["rclone", "about", "test:"], "test_remote")
        result = worker._parse_about_output(output)

        # Should still extract what it can
        assert "100 GB (but with extra text)" in result["total"] or result["total"] == "Unknown"

    @pytest.mark.qt
    def test_run_success(self, qtbot):
        """Test successful rclone command execution."""
        worker = RcloneWorker(["echo", "Total: 100 GB"], "test_remote")
        finished_called = False
        error_called = False
        result_data = None
        remote_name = None

        def on_finished(remote, result):
            nonlocal finished_called, result_data, remote_name
            finished_called = True
            remote_name = remote
            result_data = result

        def on_error(remote, error_msg):
            nonlocal error_called
            error_called = True

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)

        worker.start()
        qtbot.wait_until(lambda: finished_called or error_called, timeout=5000)

        assert finished_called
        assert not error_called
        assert remote_name == "test_remote"
        assert result_data is not None

    @pytest.mark.qt
    def test_run_error(self, qtbot):
        """Test rclone command execution with error."""
        # Use a command that will fail
        worker = RcloneWorker(["false"], "test_remote")
        finished_called = False
        error_called = False
        error_msg = None
        remote_name = None

        def on_finished(remote, result):
            nonlocal finished_called
            finished_called = True

        def on_error(remote, msg):
            nonlocal error_called, error_msg, remote_name
            error_called = True
            remote_name = remote
            error_msg = msg

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)

        worker.start()
        qtbot.wait_until(lambda: finished_called or error_called, timeout=5000)

        assert not finished_called
        assert error_called
        assert remote_name == "test_remote"
        assert error_msg is not None

    @pytest.mark.qt
    def test_run_timeout(self, qtbot):
        """Test rclone command execution timeout."""
        # Use a command that will hang (sleep longer than timeout)
        worker = RcloneWorker(["sleep", "60"], "test_remote")
        error_called = False
        error_msg = None

        def on_error(remote, msg):
            nonlocal error_called, error_msg
            error_called = True
            error_msg = msg

        worker.error.connect(on_error)

        worker.start()
        qtbot.wait_until(lambda: error_called, timeout=35000)  # Wait for timeout

        assert error_called
        assert "timed out" in error_msg.lower()

    @pytest.mark.qt
    def test_run_exception(self, qtbot):
        """Test rclone command execution with exception."""
        worker = RcloneWorker(["nonexistent_command_xyz"], "test_remote")
        error_called = False
        error_msg = None

        def on_error(remote, msg):
            nonlocal error_called, error_msg
            error_called = True
            error_msg = msg

        worker.error.connect(on_error)

        worker.start()
        qtbot.wait_until(lambda: error_called, timeout=5000)

        assert error_called
        assert error_msg is not None

    def test_parse_about_output_with_colon_in_value(self):
        """Test parsing output where value contains colon."""
        output = """Total:   100 GB: Extra info
Used:    50 GB
"""
        worker = RcloneWorker(["rclone", "about", "test:"], "test_remote")
        result = worker._parse_about_output(output)

        # Should only split on first colon
        assert "100 GB: Extra info" in result["total"]
        assert result["used"] == "50 GB"

    def test_parse_about_output_multiple_spaces(self):
        """Test parsing output with multiple spaces."""
        output = """Total:     100 GB
Used:      50 GB
Free:      50 GB
"""
        worker = RcloneWorker(["rclone", "about", "test:"], "test_remote")
        result = worker._parse_about_output(output)

        assert result["total"].strip() == "100 GB"
        assert result["used"].strip() == "50 GB"
        assert result["free"].strip() == "50 GB"
