# Check Cloud Drives

A handy PySide6 GUI application for monitoring the status of one or many cloud drives using the free open-source utility rclone for secure drive access. This app lives in your macOS menu bar and provides a sleek, modern interface to check the status of all your configured cloud drives.

**Author:** Rich Lewis - @RichLewis007

## Features

- 🎨 **Beautiful Modern UI** - Dark theme with smooth animations
- 📊 **Real-time Status** - View total, used, and free space for each drive
- 🔄 **Auto-refresh** - Automatically updates drive status at configurable intervals
- 📌 **Stay on Top** - Toggle to keep the window above other applications
- 🎯 **Menu Bar Integration** - Lives in macOS menu bar for easy access
- ⚙️ **Easy Configuration** - Simple setup dialog to select which drives to monitor
- 🔒 **Privacy First** - All private configuration stored in a local file (excluded from git)

## Requirements

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- rclone installed and configured

## Installation

1. Install `uv` if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone this repository:
```bash
git clone https://github.com/yourusername/check-cloud-drives.git
cd check-cloud-drives
```

3. Install dependencies using `uv`:
```bash
uv sync
```

This will:
- Create a virtual environment automatically
- Install all dependencies from `pyproject.toml`
- Make the project ready to run

**Alternative:** If you prefer using `pip` with a `requirements.txt` file, you can generate it first:
```bash
uv pip compile pyproject.toml -o requirements.txt
pip install -r requirements.txt
```

4. Make sure rclone is installed and configured:
```bash
rclone listremotes
```

## Usage

1. Run the application using the provided script:
```bash
./run.sh
```

Or run directly with `uv`:
```bash
uv run -m check_cloud_drives.main
```

Or activate the virtual environment and run directly:
```bash
source .venv/bin/activate  # On macOS/Linux
python -m check_cloud_drives.main
```

2. On first run, the app will:
   - Detect all available rclone remotes
   - Show a setup dialog to select which drives to monitor
   - Automatically fetch status for selected drives

3. The app will appear in your macOS menu bar. Click the icon to show/hide the window.

4. Features:
   - **Refresh All**: Manually refresh all drive statuses
   - **Add Drive**: Add additional drives to monitor
   - **Edit Names**: Click on drive names to edit display names and remote names
   - **Stay on Top**: Right-click menu bar icon to toggle "Stay on Top"

## Configuration

The application stores all configuration in `CheckCloudDrivesConfig.toml` in the project root directory. This file includes:
- List of monitored drives
- Window position and size
- Stay on top preference
- Auto-refresh interval

**Note**: This config file is excluded from git to protect your private cloud drive information.

## Drive Icons

The app supports custom SVG icons for different drive types (Google Drive, OneDrive, Dropbox, etc.). Currently using placeholder emoji icons. To add custom icons:

1. Place SVG icon files in the `assets/icons/` directory
2. Name them: `googledrive.svg`, `onedrive.svg`, `dropbox.svg`, etc.
3. The app will automatically detect and use them

## Development

The application is built with:
- **PySide6** - Modern Qt6 Python bindings
- **rclone** - Command-line tool for cloud storage
- **uv** - Fast Python package installer and resolver

### Development Setup

1. Install `uv` (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Sync dependencies:
```bash
uv sync
```

3. Run the application:
```bash
uv run -m check_cloud_drives.main
```

### Adding Dependencies

To add a new dependency:
```bash
uv add package-name
```

This will automatically update `pyproject.toml` and `uv.lock`.

### Updating Dependencies

To update all dependencies:
```bash
uv sync --upgrade
```

To update a specific package:
```bash
uv add package-name@latest
```

**Note:** The `uv.lock` file should be committed to version control to ensure reproducible builds across different environments.

### Generating requirements.txt

If you need a `requirements.txt` file for compatibility with other tools, CI/CD systems, or if you prefer using `pip` directly, you can generate it from `pyproject.toml`:

```bash
uv pip compile pyproject.toml -o requirements.txt
```

This will create a `requirements.txt` file with all dependencies and their resolved versions. You can then use it with `pip`:

```bash
pip install -r requirements.txt
```

**Note:** The `requirements.txt` file is not tracked in git. If you need it, regenerate it after updating dependencies. Using `uv sync` with `pyproject.toml` is the recommended approach and eliminates the need for `requirements.txt`.

## License

MIT License - feel free to use and modify as needed!

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

