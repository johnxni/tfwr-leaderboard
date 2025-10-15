OVER_TIME_S3 = "s3://tfwr-data/leaderboard/over_time_ms.csv"
GAPS_LATEST_S3 = "s3://tfwr-data/leaderboard/gaps_latest_ms.csv"
PERCENTILES_S3 = "s3://tfwr-data/leaderboard/percentiles.csv"


TABS = [
    "Overview",
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
    "Fastest": "#DC143C",  # crimson
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
    "Fastest": ":fast_forward:",
}

DEFAULT_COLOR = "#1f77b4"


def get_leaderboard_color(leaderboard_name):
    return COLORS.get(leaderboard_name.split()[0], DEFAULT_COLOR)


def get_emoji(leaderboard_name):
    return EMOJIS.get(leaderboard_name.split()[0], ":man_farmer:")
