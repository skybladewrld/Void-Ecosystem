"""Static v0.2 content kept out of the renderer for easy expansion."""

from models import GameEntry


GAME_LIBRARY = (
    GameEntry("SIGNAL CATCH", "ARCADE", "READY", playable=True),
    GameEntry("VOID RUNNER", "ACTION", "COMING SOON"),
    GameEntry("GLYPH TACTICS", "STRATEGY", "COMING SOON"),
)

EMULATOR_SYSTEMS = (
    ("HANDHELD 8", "NOT CONFIGURED"),
    ("HANDHELD 16", "NOT CONFIGURED"),
    ("RETRO CORE", "ADAPTER READY"),
)

FRIEND_SLOTS = (
    ("LOCAL PROFILE", "NYX-01", "ONLINE"),
    ("DIRECT LINK", "NO PEER", "SEARCHING"),
    ("VOID NODE", "NOT PAIRED", "OFFLINE"),
)

TRADE_ITEMS = (
    ("VOID SHARD", "2", "COMMON"),
    ("SPARK FRUIT", "1", "UNCOMMON"),
    ("RELIC SLOT", "EMPTY", "LOCKED"),
)

SETTING_LABELS = ("SCANLINES", "ANIMATIONS", "STATUS DETAIL")
