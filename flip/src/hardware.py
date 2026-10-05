"""Hardware boundary for desktop simulation and future Raspberry Pi adapters."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class HardwareSnapshot:
    battery_percent: float
    charging: bool
    temperature_c: float
    network: str
    platform: str
    uptime_seconds: float
    audio_available: bool = True
    input_source: str = "KEYBOARD"
    top_display: tuple[int, int] = (860, 386)
    bottom_display: tuple[int, int] = (390, 242)


class HardwareAdapter(Protocol):
    def update(self, dt: float) -> None: ...
    def snapshot(self) -> HardwareSnapshot: ...
    def set_charging(self, charging: bool) -> None: ...
    def display_metadata(self) -> dict: ...


class DesktopHardwareAdapter:
    """Changing telemetry for PC testing; replace with Pi services later."""

    def __init__(self, battery_percent: float = 100.0, charging: bool = False, *, audio_available: bool = True):
        self.battery_percent = max(0.0, min(100.0, battery_percent))
        self.charging = charging
        self.started_at = time.monotonic()
        self.audio_available = audio_available

    def update(self, dt: float) -> None:
        if self.charging:
            self.battery_percent = min(100.0, self.battery_percent + dt / 12.0)
        else:
            self.battery_percent = max(0.0, self.battery_percent - dt / 80.0)

    def set_charging(self, charging: bool) -> None:
        self.charging = charging

    def snapshot(self) -> HardwareSnapshot:
        uptime = time.monotonic() - self.started_at
        temperature = 48.0 + math.sin(uptime / 11.0) * 1.8
        return HardwareSnapshot(
            battery_percent=self.battery_percent,
            charging=self.charging,
            temperature_c=temperature,
            network="LOCAL",
            platform="DESKTOP SIM",
            uptime_seconds=uptime,
            audio_available=self.audio_available,
        )

    def display_metadata(self) -> dict:
        return {"top": (860, 386), "bottom": (390, 242), "scale": 1.0}


class MockHardwareAdapter(DesktopHardwareAdapter):
    """Deterministic adapter for tests and future platform service development."""

    def snapshot(self) -> HardwareSnapshot:
        return HardwareSnapshot(self.battery_percent, self.charging, 42.0, "OFFLINE", "MOCK", 0.0,
                                self.audio_available, "MOCK", (860, 386), (390, 242))
