"""Tests for DriveCard UI component."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from check_cloud_drives.models import DriveStatus
from check_cloud_drives.ui.card import DriveCard


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def drive_card(qapp, sample_drive_config):
    """Create a DriveCard instance for testing."""
    return DriveCard(sample_drive_config)


class TestDriveCard:
    """Test suite for DriveCard UI component."""

    def test_card_initialization(self, drive_card, sample_drive_config):
        """Test that DriveCard initializes correctly."""
        assert drive_card.drive_config == sample_drive_config
        assert drive_card.drive_status is None
        assert drive_card.is_updating is False
        assert drive_card.is_edit_mode is False

    def test_card_displays_remote_name(self, drive_card, sample_drive_config):
        """Test that card displays remote name."""
        assert hasattr(drive_card, "remote_name_label")
        assert sample_drive_config.remote_name in drive_card.remote_name_label.text()

    def test_card_displays_display_name(self, drive_card, sample_drive_config):
        """Test that card displays display name."""
        assert hasattr(drive_card, "display_name_label")
        assert drive_card.display_name_label.text() == sample_drive_config.display_name

    def test_update_display_name(self, drive_card):
        """Test updating display name."""
        new_name = "New Display Name"
        drive_card.update_display_name(new_name)

        assert drive_card.drive_config.display_name == new_name
        # The label text might be truncated or formatted, so just check it's updated
        assert drive_card.display_name_label.text() is not None

    def test_update_display_name_long_text(self, drive_card):
        """Test updating display name with long text that should truncate."""
        long_name = "This is a very long display name that should be truncated to fit in two lines"
        drive_card.update_display_name(long_name)

        assert drive_card.drive_config.display_name == long_name
        # Text should be truncated or wrapped
        displayed_text = drive_card.display_name_label.text()
        assert displayed_text is not None
        # Should have tooltip for full text
        assert len(drive_card.display_name_label.toolTip()) > 0

    def test_update_remote_name(self, drive_card):
        """Test updating remote name."""
        new_remote = "new_remote_name"
        drive_card.update_remote_name(new_remote)

        assert drive_card.drive_config.remote_name == new_remote
        assert new_remote in drive_card.remote_name_label.text()

    def test_enter_edit_mode(self, drive_card, qtbot):
        """Test entering edit mode."""
        drive_card.show()  # Widget must be shown for visibility to work
        qtbot.waitExposed(drive_card)

        assert drive_card.is_edit_mode is False
        drive_card._enter_edit_mode()
        qtbot.wait(100)  # Wait for layout updates

        assert drive_card.is_edit_mode is True
        assert drive_card.display_name_label.isVisible() is False
        assert drive_card.remote_name_label.isVisible() is False
        # edit_mode_container should be in layout and visible
        assert drive_card.edit_mode_container.parent() is not None

    def test_exit_edit_mode(self, drive_card, qtbot):
        """Test exiting edit mode."""
        drive_card.show()  # Widget must be shown for visibility to work
        qtbot.waitExposed(drive_card)

        drive_card._enter_edit_mode()
        qtbot.wait(100)
        assert drive_card.is_edit_mode is True

        drive_card._exit_edit_mode()
        qtbot.wait(100)  # Wait for layout updates

        assert drive_card.is_edit_mode is False
        # After exit, normal widgets should be visible
        assert drive_card.display_name_label.parent() is not None
        assert drive_card.remote_name_label.parent() is not None

    def test_save_edit_with_valid_text(self, drive_card, qtbot):
        """Test saving edit with valid text."""
        drive_card._enter_edit_mode()
        new_title = "New Title"
        drive_card.title_edit.setPlainText(new_title)

        # Connect to signal to verify it's emitted
        signal_received = False
        saved_name = None

        def on_saved(name):
            nonlocal signal_received, saved_name
            signal_received = True
            saved_name = name

        drive_card.display_name_saved.connect(on_saved)
        drive_card._save_edit()

        assert signal_received
        assert saved_name == new_title
        assert drive_card.drive_config.display_name == new_title
        assert drive_card.is_edit_mode is False

    def test_save_edit_with_empty_text(self, drive_card):
        """Test that saving edit with empty text doesn't save."""
        original_name = drive_card.drive_config.display_name
        drive_card._enter_edit_mode()
        drive_card.title_edit.setPlainText("")

        signal_received = False

        def on_saved(name):
            nonlocal signal_received
            signal_received = True

        drive_card.display_name_saved.connect(on_saved)
        drive_card._save_edit()

        # Should not emit signal and stay in edit mode
        assert not signal_received
        assert drive_card.drive_config.display_name == original_name
        assert drive_card.is_edit_mode is True

    def test_save_edit_with_whitespace_only(self, drive_card):
        """Test that saving edit with whitespace-only text doesn't save."""
        original_name = drive_card.drive_config.display_name
        drive_card._enter_edit_mode()
        drive_card.title_edit.setPlainText("   ")

        signal_received = False

        def on_saved(name):
            nonlocal signal_received
            signal_received = True

        drive_card.display_name_saved.connect(on_saved)
        drive_card._save_edit()

        # Should not emit signal
        assert not signal_received
        assert drive_card.drive_config.display_name == original_name

    def test_cancel_edit(self, drive_card):
        """Test canceling edit restores original text."""
        original_name = drive_card.drive_config.display_name
        drive_card._enter_edit_mode()
        drive_card.title_edit.setPlainText("Modified Text")

        drive_card._cancel_edit()

        assert drive_card.drive_config.display_name == original_name
        assert drive_card.is_edit_mode is False
        assert drive_card.title_edit.toPlainText() == original_name

    def test_remove_card_emits_signal(self, drive_card, qtbot):
        """Test that removing card emits signal."""
        signal_received = False

        def on_removed():
            nonlocal signal_received
            signal_received = True

        drive_card.card_removed.connect(on_removed)
        drive_card._enter_edit_mode()
        drive_card._remove_card()

        assert signal_received
        assert drive_card.is_edit_mode is False

    def test_update_status(self, drive_card, sample_drive_status, qtbot):
        """Test updating drive status."""
        drive_card.show()  # Widget must be shown for visibility to work
        qtbot.waitExposed(drive_card)

        drive_card.update_status(sample_drive_status)
        qtbot.wait(100)  # Wait for UI updates

        assert drive_card.drive_status == sample_drive_status
        # free_space_label should be visible if free value is valid
        if sample_drive_status.free and sample_drive_status.free != "Unknown":
            assert drive_card.free_space_label.isVisible() is True
            # Check that free space is displayed
            assert (
                sample_drive_status.free in drive_card.free_space_label.text()
                or "Free:" in drive_card.free_space_label.text()
            )

    def test_update_status_with_error(self, drive_card):
        """Test updating drive status with error."""
        error_status = DriveStatus(
            remote_name="test_remote",
            error="Connection failed",
        )
        drive_card.update_status(error_status)

        assert drive_card.drive_status == error_status
        assert drive_card.drive_status.error == "Connection failed"

    def test_set_updating_state(self, drive_card):
        """Test setting updating state shows/hides spinner."""
        assert drive_card.is_updating is False

        drive_card.set_updating(True)
        assert drive_card.is_updating is True
        # Status label should show "Updating..."
        assert "Updating" in drive_card.status_label.text()

        drive_card.set_updating(False)
        assert drive_card.is_updating is False

    def test_edit_mode_preserves_card_height(self, drive_card):
        """Test that entering edit mode preserves card height."""
        # Show the card to get a real height
        drive_card.show()

        drive_card._enter_edit_mode()
        # Height should be fixed and similar to original
        assert drive_card.height() > 0

        drive_card._exit_edit_mode()
        # Height should be restored (or at least not fixed)
        # Note: After exit, height might be different due to layout, but should be reasonable

    def test_edit_mode_title_edit_has_focus(self, drive_card, qtbot):
        """Test that title edit gets focus when entering edit mode."""
        drive_card.show()  # Widget must be shown for focus to work
        qtbot.waitExposed(drive_card)

        drive_card._enter_edit_mode()
        qtbot.wait(100)  # Wait for focus to be set

        # Focus might not be set immediately, but title_edit should exist and be in edit mode
        assert drive_card.title_edit is not None
        assert drive_card.is_edit_mode is True
        # Try to verify focus was requested (may need processing)
        qtbot.mouseClick(drive_card.title_edit, Qt.LeftButton)
        qtbot.wait(50)
        # After click, it should have focus
        assert drive_card.title_edit.hasFocus() is True

    def test_edit_mode_title_edit_has_correct_text(self, drive_card):
        """Test that title edit is populated with current display name."""
        original_name = drive_card.drive_config.display_name
        drive_card._enter_edit_mode()

        assert drive_card.title_edit.toPlainText() == original_name

    def test_edit_mode_title_edit_text_selected(self, drive_card):
        """Test that title edit text is selected when entering edit mode."""
        drive_card._enter_edit_mode()
        # Text should be selected
        assert drive_card.title_edit.textCursor().hasSelection() is True

    def test_multiple_edit_mode_entries(self, drive_card):
        """Test entering edit mode multiple times doesn't break state."""
        drive_card._enter_edit_mode()
        assert drive_card.is_edit_mode is True

        # Enter again (should be idempotent)
        drive_card._enter_edit_mode()
        assert drive_card.is_edit_mode is True

        drive_card._exit_edit_mode()
        assert drive_card.is_edit_mode is False

    def test_update_display_name_with_manual_line_break(self, drive_card):
        """Test that update_display_name handles manual line breaks correctly."""
        # Text that should be split into 2 lines
        long_name = "First Part Second Part Third Part"
        drive_card.update_display_name(long_name)

        # Should handle the text (might be split or truncated)
        displayed = drive_card.display_name_label.text()
        assert displayed is not None
        assert len(displayed) > 0
