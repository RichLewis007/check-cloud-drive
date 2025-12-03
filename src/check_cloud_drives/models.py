"""Data models for cloud drive configuration and status."""

from dataclasses import asdict, dataclass


@dataclass
class DriveConfig:
    """Configuration for a single cloud drive."""

    remote_name: str
    display_name: str
    drive_type: str = "unknown"  # "googledrive", "onedrive", "dropbox", etc.
    enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DriveConfig":
        return cls(**data)


@dataclass
class DriveStatus:
    """Status information for a cloud drive."""

    remote_name: str
    total: str = "Unknown"
    used: str = "Unknown"
    free: str = "Unknown"
    trash: str = "Unknown"
    other: str = "Unknown"
    objects: str = "Unknown"
    last_updated: str = "Never"
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DriveStatus":
        return cls(**data)
