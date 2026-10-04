"""Platform-owned content definitions for the Void Flip shell."""

from models import GameEntry, ItemDefinition, RelicDefinition, RelicRecipe


ITEMS = {
    item.item_id: item
    for item in (
        ItemDefinition("spark_fruit", "SPARK FRUIT", "FOOD", "COMMON", "Restores fullness and a little energy.", energy=10, fullness=26, joy=4, bond=1),
        ItemDefinition("moon_biscuit", "MOON BISCUIT", "FOOD", "UNCOMMON", "A favorite treat that restores joy.", fullness=18, joy=22, bond=2),
        ItemDefinition("starlight_tea", "STARLIGHT TEA", "FOOD", "RARE", "A bright tonic for long expeditions.", energy=28, fullness=8, joy=10, bond=1),
        ItemDefinition("repair_gel", "REPAIR GEL", "MEDICINE", "RARE", "Repairs health after neglect or hard training.", health=32, joy=-2),
        ItemDefinition("static_toy", "STATIC TOY", "CARE", "UNCOMMON", "A reusable-looking toy; consumed until crafting arrives.", energy=-3, joy=30, bond=3),
        ItemDefinition("void_shard", "VOID SHARD", "MATERIAL", "COMMON", "Stable crafting material used for future relic work.", usable=False),
        ItemDefinition("prism_seed", "PRISM SEED", "MATERIAL", "RARE", "A rare exploration find for future evolution paths.", usable=False),
    )
}


RELICS = {
    relic.relic_id: relic
    for relic in (
        RelicDefinition("ember_core", "EMBER CORE", "COMMON", "CORE", "Raises maximum energy by 20.", energy_cap_bonus=20),
        RelicDefinition("echo_lens", "ECHO LENS", "UNCOMMON", "LENS", "Records patterns and grants 15% more XP.", xp_multiplier=1.15),
        RelicDefinition("anchor_sigil", "ANCHOR SIGIL", "RARE", "CHARM", "Slows all need decay by 30%.", decay_multiplier=0.70),
        RelicDefinition("nurture_knot", "NURTURE KNOT", "RARE", "CHARM", "Care items and positive actions are 25% stronger.", care_multiplier=1.25, bond_bonus=1),
        RelicDefinition("prism_compass", "PRISM COMPASS", "EPIC", "LENS", "Adds 30% to exploration find chance.", explore_find_bonus=0.30),
        RelicDefinition("null_crown", "NULL CROWN", "LEGENDARY", "CORE", "High-bond relic: 25% more XP and +2 bond per action.", xp_multiplier=1.25, bond_bonus=2),
    )
}

RELIC_RECIPES = (
    RelicRecipe("nurture_knot", {"void_shard": 3, "moon_biscuit": 1}),
    RelicRecipe("prism_compass", {"void_shard": 4, "prism_seed": 2}),
    RelicRecipe("null_crown", {"void_shard": 8, "prism_seed": 4, "starlight_tea": 2}),
)


CARE_ACTIONS = (
    ("PLAY", "JOY +20", "Active bonding session"),
    ("REST", "ENERGY +32", "Recover energy and health"),
    ("TRAIN", "XP +24", "High effort progression"),
    ("EXPLORE", "FIND ITEMS", "Risk energy for discoveries"),
    ("COMFORT", "BOND +4", "Gentle low-cost attention"),
)

EXPLORE_REWARDS = ("spark_fruit", "moon_biscuit", "starlight_tea", "void_shard", "prism_seed")


GAME_LIBRARY = (
    GameEntry("merge_2048", "VOID MERGE 2048", "PUZZLE", "PLAYABLE", "Merge matching values, plan the grid, and reach the 2048 core.", playable=True),
    GameEntry("maze_shift", "MAZE SHIFT", "MAZE CHASE", "DESIGN", "Original shifting-maze chase with Voidling rescue objectives."),
    GameEntry("starfall_wing", "STARFALL WING", "SPACE SHOOTER", "DESIGN", "Formation shooter with upgrade routes and boss patterns."),
    GameEntry("void_garden", "VOID GARDEN", "AFK", "PLANNED", "Offline resource ecology tied to careful return visits."),
    GameEntry("relay_forge", "RELAY FORGE", "CLICKER", "PLANNED", "Combo-driven crafting instead of empty number inflation."),
    GameEntry("signal_serpent", "SIGNAL SERPENT", "ARCADE", "PLANNED", "Snake with hazards, routes, and score missions."),
    GameEntry("blackglass", "BLACKGLASS CHECKERS", "BOARD", "PLANNED", "Full checkers with local AI and two-player play.", "1-2P"),
    GameEntry("constellation", "CONSTELLATION HOP", "BOARD", "PLANNED", "Chinese-checkers-inspired multiplayer for direct links.", "2-6P"),
    GameEntry("void_party", "VOID PARTY", "PARTY", "PLANNED", "A rotating collection of local multiplayer challenges.", "2-4P"),
    GameEntry("community", "COMMUNITY GAMES", "PLATFORM", "PLANNED", "Permissioned packages with clear trust labels.", "VARIES"),
)


EMULATOR_SYSTEMS = (
    ("MONSTER RPG PROFILE", "NOT CONFIGURED", "User-supplied ROM only"),
    ("HANDHELD 8/16", "ADAPTER READY", "Core selection pending"),
    ("SAVE VAULT", "LOCAL ONLY", "No cloud dependency"),
)

FRIEND_SLOTS = (
    ("LOCAL PROFILE", "NYX-01", "ONLINE"),
    ("DIRECT LINK", "NO PEER", "SEARCHING"),
    ("VOID NODE", "NOT PAIRED", "OFFLINE"),
)

SETTING_LABELS = ("SCANLINES", "ANIMATIONS", "STATUS DETAIL", "SIM CHARGER")
