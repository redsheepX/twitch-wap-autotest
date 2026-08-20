from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class InterruptionDecision(StrEnum):
    DISMISS = "dismiss"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class Interruption:
    name: str
    blocking: bool = True


@dataclass(frozen=True)
class ChannelReadiness:
    channel_url: str
    main_content_visible: bool
    blocking_interruption_present: bool
    streamer_name_visible: bool

    @property
    def observable(self) -> bool:
        return (
            self.main_content_visible
            and not self.blocking_interruption_present
            and self.streamer_name_visible
        )


@dataclass(frozen=True)
class Evidence:
    screenshot_path: Path
    channel_url: str
