# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive unit test suite with 64 tests covering:
  - ConfigManager (config loading/saving, persistence, TOML handling)
  - DriveConfig and DriveStatus models (validation, serialization)
  - RcloneWorker integration (command execution, output parsing)
  - DriveCard UI component (edit mode, status updates, display)
- pytest testing framework with pytest-qt for Qt widget testing
- Test fixtures and shared test utilities in `tests/conftest.py`
- Test documentation in `tests/README.md`
- pytest configuration in `pytest.ini`

### Changed

- Added pytest, pytest-qt, and pytest-mock to dev dependencies

## [0.1.0] - 2025-10-15

### Added

- **Core Application**

  - PySide6 GUI application for monitoring cloud drives via rclone
  - macOS menu bar integration with system tray icon
  - Main window with scrollable drive cards layout
  - Application modal dialogs for better UX

- **Drive Management**

  - Initial setup dialog to select which drives to monitor
  - Add drive dialog with manual remote entry
  - Support for multiple cloud drive types (Google Drive, OneDrive, Dropbox, ProtonDrive, etc.)
  - Automatic detection of available rclone remotes
  - Drive type detection from remote names
  - Display name auto-generation from remote names
  - Remove drive functionality with confirmation

- **Drive Cards**

  - Individual drive card widgets with custom styling
  - Drive status display (total, used, free space, objects, trash, other)
  - Free space prominently displayed at bottom center of card
  - Custom SVG icon support for different drive types
  - Icon loading with fallback to emoji placeholders
  - Two-line title display with automatic truncation
  - Relative timestamp display ("X minutes ago") with auto-update
  - Loading spinner animation during status updates
  - Hover effects and visual feedback
  - Card drag and drop reordering
  - Drag preview with visual feedback
  - Edit mode for drive card titles
  - Inline title editing with Save/Cancel buttons
  - Remove card button in edit mode
  - Error state display for failed status updates

- **Status Updates**

  - Real-time drive status fetching via rclone
  - Auto-refresh at configurable intervals (default: 300 seconds)
  - Manual refresh all drives button
  - Individual drive status updates
  - Background worker threads for non-blocking updates
  - Status update indicators and animations
  - Error handling for failed rclone commands
  - Timeout handling for long-running commands

- **Configuration**

  - TOML-based configuration file (`CheckCloudDrivesConfig.toml`)
  - Drive list persistence
  - Window geometry saving and restoration
  - Stay on top preference
  - Auto-refresh interval setting
  - Drive order persistence
  - Run at system startup setting (placeholder)
  - Privacy-first: config file excluded from git

- **UI/UX Features**

  - Modern light theme with clean design
  - Custom font support (Atkinson Hyperlegible Mono Nerd Font)
  - Bundled font loading from zip archive
  - Consistent button styling and sizing
  - Responsive layout with scrollable content
  - Settings page with auto-refresh configuration
  - Stay on top toggle in menu bar context menu
  - Window position and size persistence
  - Smooth animations and transitions
  - Visual feedback for user interactions

- **Code Quality**

  - Ruff linter and formatter configuration
  - Code formatting script (`scripts/ruff.sh`)
  - Consistent code style across project
  - Type hints and documentation

- **Documentation**
  - README with installation and usage instructions
  - GitHub Pages documentation site
  - Example configuration files
  - Asset documentation (icons, fonts)

### Changed

- Improved dialog modal behavior (application modal)
- Enhanced button height consistency across dialogs
- Improved icon display and text placement
- Fixed font loading and asset paths
- Memory leak fixes for worker threads
- Improved card rearrangement logic
- Enhanced add dialog with better remote ordering
- Removed visual artifacts from drag and drop (grey background)
- Improved app handler for edge cases with "stay on top" feature
- Better error handling and user feedback

### Fixed

- Memory leak in RcloneWorker threads
- Font loading path resolution issues
- Asset path resolution for bundled resources
- Card drag and drop visual artifacts
- Dialog positioning when "stay on top" is active
- Button height inconsistencies across UI components
- Icon and text placement alignment
- Card reordering logic improvements

## [0.0.9] - 2025-10-01

### Changed

- Improved dialog modal behavior (application modal)
- Enhanced button height consistency across dialogs
- Improved icon display and text placement
- Better error handling and user feedback

### Fixed

- Card drag and drop visual artifacts (removed grey background)
- Dialog positioning when "stay on top" is active
- Button height inconsistencies across UI components
- Icon and text placement alignment
- Card reordering logic improvements

## [0.0.8] - 2025-09-20

### Changed

- Improved card rearrangement logic
- Enhanced add dialog with better remote ordering
- Removed redundant code

### Fixed

- Memory leak in RcloneWorker threads

## [0.0.7] - 2025-09-10

### Added

- GitHub Pages documentation site
- Auto-deploy GitHub Actions workflow

### Changed

- Updated documentation and landing page

## [0.0.6] - 2025-08-25

### Added

- Bundled font loading from zip archive
- Font cleanup on application exit
- Support for multiple font variants (Regular, Bold, Italic, etc.)

### Fixed

- Font loading path resolution issues
- Asset path resolution for bundled resources

## [0.0.5] - 2025-08-15

### Added

- Ruff linter and formatter configuration
- Code formatting script (`scripts/ruff.sh`)
- Consistent code style across project

### Changed

- Code formatting and linting improvements
- Type hints and documentation enhancements

## [0.0.4] - 2025-08-01

### Added

- Settings page with auto-refresh configuration
- Stay on top toggle in menu bar context menu
- Window position and size persistence

### Changed

- Improved UI consistency
- Enhanced user experience

## [0.0.3] - 2025-07-20

### Added

- Drag and drop card reordering
- Drag preview with visual feedback
- Edit mode for drive card titles
- Inline title editing with Save/Cancel buttons
- Remove card button in edit mode

### Changed

- Improved card layout and styling
- Enhanced visual feedback for interactions

## [0.0.2] - 2025-07-05

### Added

- Custom SVG icon support for different drive types
- Icon loading with fallback to emoji placeholders
- Two-line title display with automatic truncation
- Relative timestamp display ("X minutes ago") with auto-update
- Loading spinner animation during status updates
- Error state display for failed status updates
- Free space prominently displayed at bottom center of card

### Changed

- Enhanced drive card visual design
- Improved status information layout

## [0.0.1] - 2025-06-15

### Added

- Initial project setup
- Basic rclone integration
- Core drive status fetching functionality
- Basic UI structure
- PySide6 GUI application foundation
- macOS menu bar integration with system tray icon
- Main window with scrollable drive cards layout
- Initial setup dialog to select which drives to monitor
- Add drive dialog with manual remote entry
- Support for multiple cloud drive types
- Automatic detection of available rclone remotes
- Drive type detection from remote names
- Display name auto-generation from remote names
- Real-time drive status fetching via rclone
- Auto-refresh at configurable intervals
- Manual refresh all drives button
- Background worker threads for non-blocking updates
- TOML-based configuration file
- Drive list persistence
- Window geometry saving and restoration
- Modern light theme with clean design

[Unreleased]: https://github.com/RichLewis007/check-cloud-drives/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/RichLewis007/check-cloud-drives/releases/tag/v0.1.0
[0.0.9]: https://github.com/RichLewis007/check-cloud-drives/releases/tag/v0.0.9
[0.0.8]: https://github.com/RichLewis007/check-cloud-drives/releases/tag/v0.0.8
[0.0.7]: https://github.com/RichLewis007/check-cloud-drives/releases/tag/v0.0.7
[0.0.6]: https://github.com/RichLewis007/check-cloud-drives/releases/tag/v0.0.6
[0.0.5]: https://github.com/RichLewis007/check-cloud-drives/releases/tag/v0.0.5
[0.0.4]: https://github.com/RichLewis007/check-cloud-drives/releases/tag/v0.0.4
[0.0.3]: https://github.com/RichLewis007/check-cloud-drives/releases/tag/v0.0.3
[0.0.2]: https://github.com/RichLewis007/check-cloud-drives/releases/tag/v0.0.2
[0.0.1]: https://github.com/RichLewis007/check-cloud-drives/releases/tag/v0.0.1
