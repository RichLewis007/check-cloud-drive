"""Rclone command execution and parsing.

Author: Rich Lewis - @RichLewis007
"""

import subprocess

from PySide6.QtCore import QThread, Signal


class RcloneWorker(QThread):
    """Worker thread for executing rclone commands."""

    finished = Signal(str, dict)  # remote_name, result dict
    error = Signal(str, str)  # remote_name, error message

    def __init__(self, command: list[str], remote_name: str = ""):
        super().__init__()
        self.command = command
        self.remote_name = remote_name

    def run(self):
        try:
            result = subprocess.run(self.command, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                output = result.stdout
                parsed = self._parse_about_output(output)
                self.finished.emit(self.remote_name, parsed)
            else:
                self.error.emit(self.remote_name, result.stderr or "Unknown error")
        except subprocess.TimeoutExpired:
            self.error.emit(self.remote_name, "Command timed out")
        except Exception as e:
            self.error.emit(self.remote_name, str(e))

    def _parse_about_output(self, output: str) -> dict:
        """Parse rclone about output into structured data."""
        result = {
            "total": "Unknown",
            "used": "Unknown",
            "free": "Unknown",
            "trash": "Unknown",
            "other": "Unknown",
            "objects": "Unknown",
            "raw": output,
        }

        lines = output.split("\n")
        for line in lines:
            line_lower = line.lower().strip()
            if "total:" in line_lower:
                result["total"] = line.split(":", 1)[1].strip() if ":" in line else "Unknown"
            elif "used:" in line_lower:
                result["used"] = line.split(":", 1)[1].strip() if ":" in line else "Unknown"
            elif "free:" in line_lower:
                result["free"] = line.split(":", 1)[1].strip() if ":" in line else "Unknown"
            elif "trash:" in line_lower:
                result["trash"] = line.split(":", 1)[1].strip() if ":" in line else "Unknown"
            elif "other:" in line_lower:
                result["other"] = line.split(":", 1)[1].strip() if ":" in line else "Unknown"
            elif "objects:" in line_lower:
                result["objects"] = line.split(":", 1)[1].strip() if ":" in line else "Unknown"

        return result
