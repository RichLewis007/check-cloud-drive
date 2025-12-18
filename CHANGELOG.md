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

- **Release Summary**
  - Complete feature set for monitoring cloud drives via rclone
  - Full UI/UX implementation with modern design
  - Comprehensive configuration management
  - Production-ready application

### Changed

- Final polish and refinements for production release
- Code cleanup and optimization

## [0.0.9] - 2025-10-01

### Added

- Application modal dialogs for better UX (prevents interaction with main window)
- Enhanced visual feedback for user interactions
- Smooth animations and transitions throughout the UI
- Consistent button styling across all dialogs and pages

### Changed

- Improved dialog modal behavior to be application-modal instead of window-modal
- Standardized button heights across all UI components using reference button sizing
- Refined icon and text placement for better visual alignment
- Enhanced error handling with user-friendly messages

### Fixed

- Card drag and drop visual artifacts (removed grey background on drop)
- Dialog positioning edge cases when "stay on top" is active
- Button height inconsistencies between different dialogs and pages
- Icon and text placement misalignment issues
- App handler edge cases when returning to app with "stay on top" enabled

## [0.0.8] - 2025-09-20

### Added

- Drive order persistence in configuration file
- Card rearrangement preserves order across app restarts
- Remote ordering in add dialog matches current card display order

### Changed

- Refactored card reordering logic for better reliability
- Improved add dialog to show remotes in same order as displayed cards
- Code cleanup: removed redundant and duplicate code paths

### Fixed

- Memory leak in RcloneWorker threads (workers now properly cleaned up)
- Card reordering edge cases when dragging between positions
- Add dialog not maintaining correct remote order

## [0.0.7] - 2025-09-10

### Added

- GitHub Pages documentation site with modern design
- Auto-deploy GitHub Actions workflow for documentation
- Example configuration files (config.example.toml, config.example.json)
- Comprehensive asset documentation (icons, fonts)

### Changed

- Updated documentation and landing page with feature highlights
- Enhanced README with detailed installation and usage instructions
- Improved documentation structure and navigation

## [0.0.6] - 2025-08-25

### Added

- Bundled font loading system from zip archive
- Automatic font extraction to temporary cache directory
- Font cleanup on application exit to prevent file system clutter
- Support for multiple font variants (Regular, Bold, Italic, BoldItalic, Medium)
- Custom font support (Atkinson Hyperlegible Mono Nerd Font) for consistent UI appearance
- Font fallback mechanism if bundled fonts unavailable

### Changed

- Font loading now happens at application startup before UI creation
- Improved font path resolution for both development and packaged distributions

### Fixed

- Font loading path resolution issues in different environments
- Asset path resolution for bundled resources in packaged applications
- Font file cleanup on application crash or unexpected exit

## [0.0.5] - 2025-08-15

### Added

- Ruff linter and formatter configuration with project-specific rules
- Code formatting script (`scripts/ruff.sh`) with multiple operation modes
- Consistent code style enforcement across entire project
- Type hints throughout codebase for better IDE support
- Comprehensive docstrings for all modules and classes

### Changed

- Applied code formatting to entire codebase
- Enhanced type hints for better static analysis
- Improved code documentation and inline comments
- Standardized import ordering and organization

## [0.0.4] - 2025-08-01

### Added

- Settings page accessible from main window
- Auto-refresh interval configuration (configurable in seconds)
- Stay on top toggle in menu bar context menu
- Window position and size persistence across sessions
- Auto-refresh interval setting saved to configuration
- Stay on top preference persisted in configuration file
- Run at system startup setting (placeholder for future implementation)

### Changed

- Improved UI consistency across all pages and dialogs
- Enhanced user experience with persistent preferences
- Configuration management now handles all user preferences
- Settings page integrated into main window layout

## [0.0.3] - 2025-07-20

### Added

- Drag and drop card reordering functionality
- Visual drag preview with card opacity changes during drag
- Edit mode for drive card titles (accessed via gear icon)
- Inline title editing with multi-line text field
- Save and Cancel buttons in edit mode
- Remove card button in edit mode (red button at bottom)
- Remove drive functionality with automatic removal from configuration
- Customizable display names for drives (independent of remote names)
- Card height preservation during edit mode transitions

### Changed

- Improved card layout and styling for better visual hierarchy
- Enhanced visual feedback for drag and drop interactions
- Card hover effects with border color changes
- Edit mode maintains card dimensions to prevent layout shifts

## [0.0.2] - 2025-07-05

### Added

- Custom SVG icon support for different drive types (Google Drive, OneDrive, Dropbox, etc.)
- Icon loading system with automatic detection and fallback to emoji placeholders
- Two-line title display with automatic word wrapping and truncation
- Relative timestamp display ("X minutes ago") with automatic updates every minute
- Loading spinner animation during status updates (orange rotating arc)
- Error state display for failed status updates with red error messages
- Free space prominently displayed at bottom center of card (red, bold, one decimal place)
- Comprehensive drive status display (total, used, free space, objects, trash, other)
- Individual drive card widgets with custom QFrame styling
- Modern light theme with clean white cards and subtle borders
- Responsive layout with scrollable content area
- Card maximum width constraint (400px) to prevent overly wide cards

### Changed

- Enhanced drive card visual design with rounded corners and hover effects
- Improved status information layout with better spacing and alignment
- Better card styling with consistent padding and margins
- Hover effects with border color change to blue

## [0.0.1] - 2025-06-15

### Added

- Initial project setup with PySide6 and modern Python packaging (pyproject.toml)
- PySide6 GUI application foundation with QMainWindow architecture
- macOS menu bar integration with system tray icon
- Main window with scrollable drive cards layout using QScrollArea
- Basic rclone integration via subprocess calls
- Core drive status fetching functionality using `rclone about` command
- Real-time drive status fetching via rclone with structured output parsing
- Background worker threads (QThread) for non-blocking status updates
- Status update indicators and animations (loading states)
- Error handling for failed rclone commands with user-friendly messages
- Timeout handling for long-running commands (30 second timeout)
- Initial setup dialog to select which drives to monitor (first run)
- Add drive dialog with manual remote entry and validation
- Support for multiple cloud drive types (Google Drive, OneDrive, Dropbox, ProtonDrive, etc.)
- Automatic detection of available rclone remotes via `rclone listremotes`
- Drive type detection from remote names using pattern matching
- Display name auto-generation from remote names with formatting
- Auto-refresh at configurable intervals (default: 300 seconds)
- Manual refresh all drives button in main window
- Individual drive status updates with per-card update indicators
- TOML-based configuration file (`CheckCloudDrivesConfig.toml`)
- Drive list persistence across application restarts
- Window geometry saving and restoration (position and size)
- Privacy-first approach: config file excluded from git
- Basic UI structure with header, content area, and action buttons
- Configuration manager class for loading and saving settings
- Data models for DriveConfig and DriveStatus using dataclasses
- RcloneWorker class for async status fetching

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
