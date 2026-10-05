"""Serializable v0.4 Void Link concepts. No networking is implemented here."""

from dataclasses import dataclass, field


ProtocolVersion = str
DeviceID = str


@dataclass(frozen=True)
class LocalProfileSummary:
    display_name: str
    voidling_name: str
    level: int
    badge_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class GameSession:
    session_id: str
    game_id: str
    host_device_id: DeviceID
    protocol_version: ProtocolVersion = "0.1"


@dataclass(frozen=True)
class PeerPresence:
    device_id: DeviceID
    profile: LocalProfileSummary
    status: str = "OFFLINE"


@dataclass(frozen=True)
class TradeOffer:
    offer_id: str
    sender_device_id: DeviceID
    offered_cosmetic_ids: tuple[str, ...] = field(default_factory=tuple)
    requested_cosmetic_ids: tuple[str, ...] = field(default_factory=tuple)
