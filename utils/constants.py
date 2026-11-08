OVER_TIME_S3 = "s3://tfwr-data/leaderboard/over_time_ms.csv"
GAPS_LATEST_S3 = "s3://tfwr-data/leaderboard/gaps_latest_ms.csv"
PERCENTILES_S3 = "s3://tfwr-data/leaderboard/percentiles.csv"


TABS = [
    "Overview",
    # The Miner Was Replaced DLC, in rough unlock order (no official order is
    # published; inferred from Steam achievement completion rates).
    "Ores",
    "Ores Single",
    "Rice",
    "Rice Single",
    "Bamboo",
    "Bamboo Single",
    "Mushrooms",
    "Mushrooms Single",
    "Dynamite",
    "Dynamite Single",
    "Treasure Map",
    "Pyramids",
    "Pyramids Single",
    "Fastest Underground Reset",
    # Base game
    "Hay",
    "Hay Single",
    "Wood",
    "Wood Single",
    "Carrots",
    "Carrots Single",
    "Pumpkins",
    "Pumpkins Single",
    "Cactus",
    "Cactus Single",
    "Maze",
    "Maze Single",
    "Sunflowers",
    "Sunflowers Single",
    "Dinosaur",
    "Fastest Reset",
]

COLORS = {
    "Hay": "#DAA520",  # goldenrod
    "Wood": "#8B4513",  # saddle brown
    "Carrots": "#FFB347",  # light orange
    "Pumpkins": "#FFA500",  # orange
    "Cactus": "#2E8B57",  # sea green
    "Maze": "#006400",  # dark green
    "Sunflowers": "#FFD700",  # gold
    "Dinosaur": "#808080",  # gray
    "Fastest Reset": "#DC143C",  # crimson
    "Ores": "#708090",  # slate gray
    "Rice": "#F5DEB3",  # wheat
    "Bamboo": "#7CB342",  # bamboo green
    "Mushrooms": "#B22222",  # firebrick
    "Dynamite": "#FF4500",  # orange red
    "Treasure Map": "#C19A6B",  # parchment brown
    "Pyramids": "#EDC9AF",  # desert sand
    "Fastest Underground Reset": "#6A5ACD",  # slate blue
}

EMOJIS = {
    "Hay": ":ear_of_rice:",
    "Wood": ":evergreen_tree:",
    "Carrots": ":carrot:",
    "Pumpkins": ":jack_o_lantern:",
    "Cactus": ":cactus:",
    "Maze": ":jigsaw:",
    "Sunflowers": ":sunflower:",
    "Dinosaur": ":bone:",
    "Fastest Reset": ":fast_forward:",
    "Ores": ":pick:",
    "Rice": ":rice:",
    "Bamboo": ":bamboo:",
    "Mushrooms": ":mushroom:",
    "Dynamite": ":firecracker:",
    "Treasure Map": ":world_map:",
    "Pyramids": ":small_red_triangle:",
    "Fastest Underground Reset": ":arrow_double_down:",
}

DEFAULT_COLOR = "#1f77b4"


def _category(leaderboard_name):
    return leaderboard_name.removesuffix(" Single")


def get_leaderboard_color(leaderboard_name):
    return COLORS.get(_category(leaderboard_name), DEFAULT_COLOR)


def get_emoji(leaderboard_name):
    return EMOJIS.get(_category(leaderboard_name), ":man_farmer:")
