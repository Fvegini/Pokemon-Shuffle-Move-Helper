from pathlib import Path


BARRIER_PREFIX = "Barrier_"

STAGE_FLANN_IMAGE_PATH = r"FLANN.png"
LAST_BOARD_IMAGE_PATH = r"last_board.png"
LAST_SCREEN_IMAGE_PATH = r"last_screen.png"
IMAGES_BARRIER_PATH = r"assets\icons_barrier"
IMAGES_EXTRA_PATH = r"assets\icons_extra"
IMAGES_PATH = r"assets\icons_processed"
ASSETS_PATH = r"assets"
BARRIER_TYPE_REAL = "Real"
BARRIER_TYPE_FAKE = "Fake"

GRADING_TOTAL_SCORE = "grading.score"
GRADING_MEGA_PROGRESS = "grading.megaprogress"
GRADING_WEEKEND_MEOWTH = "WeekendMeowth"

move_strategy = {
    "grading.score": "Total Score",
    "grading.totalblocks": "Total Blocks",
    "grading.disruptions": "Disruptions",
    "grading.mindisruptions": "Low Disrupt.",
    "grading.combos": "Combos",
    "grading.noneorall": "None or All",
    "grading.megaprogress": "Mega Progress",
    "grading.coordinate": "Coordinates",
    "WeekendMeowth": "WeekendMeowth",
    "037MeowthEarlyGame": "037MeowthEarlyGame",
    "037MeowthEndGame": "037MeowthEndGame"
}

move_stages = {
    "NORMAL": "NORMAL",
    "FIRE": "FIRE",
    "WATER": "WATER",
    "GRASS": "GRASS",
    "ELECTRIC": "ELECTRIC",
    "ICE": "ICE",
    "FIGHTING": "FIGHTING",
    "POISON": "POISON",
    "GROUND": "GROUND",
    "FLYING": "FLYING",
    "PSYCHIC": "PSYCHIC",
    "BUG": "BUG",
    "ROCK": "ROCK",
    "GHOST": "GHOST",
    "DRAGON": "DRAGON",
    "DARK": "DARK",
    "STEEL": "STEEL",
    "FAIRY": "FAIRY",
    "NONE": "NONE",
    "SP_084": "MEOWTH COIN MANIA",
    "037": "STAGE 37"
}
downscale_res = (128, 128)

STAGE_TO_IMAGE = {
    "STAGE 37": "052",
    "STAGE 38": "453",
    "STAGE 39": "222",
}

# This is a bad name. These will change from phone to phone
# depending on how big the top status bar is etc.. These are just
# hardcode values for my phones.
RESOLUTIONS = {
    "1440x3120": {
        # Stage Selection
        "StageSelectionArea": (320, 550, 1120, 2600),
        "HeartTimer": (75, 190, 255, 250),
        "Hearts": (355, 190, 480, 250),
        "Continue": (420, 2770, 1020, 2870),
        "Start!": (420, 2770, 1020, 2870),
        "No": (1000, 2390, 1340, 2490),
        "To Map": (420, 2770, 1020, 2870),
        # Stage
        "Board": (20, 1540, 1415, 2935),
        "Stage": (45, 225, 320, 285),
        "Score": (45, 385, 320, 450),
        "MovesLeft": (45, 1285, 390, 1375),
    },
    "1080x2160": {
        # Stage Selection
        "StageSelectionArea": (240, 400, 840, 1800),
        "HeartTimer": (58, 112, 190, 155),
        "Hearts": (265, 112, 357, 155),
        "Continue": (340, 1890, 740, 1970),
        "Start!": (340, 1890, 740, 1970),
        "No": (780, 1690, 990, 1760),
        "To Map": (340, 1890, 740, 1970),
        # Stage
        "Board": (17, 968, 1064, 2015),
        "Stage": (35, 140, 240, 185),
        "Score": (35, 260, 240, 305),
        "MovesLeft": (35, 775, 300, 845),
    }
}


CURRENT_HEARTS_LIST = [
    Path(r"assets\adb\heart_9.png"),
    Path(r"assets\adb\heart_5.png"),
    Path(r"assets\adb\heart_4.png"),
    Path(r"assets\adb\heart_3.png"),
    Path(r"assets\adb\heart_2.png"),
    Path(r"assets\adb\heart_1.png"),
    Path(r"assets\adb\heart_0.png"),
]

CURRENT_STAGE_IMAGE = r"assets\adb\auto\01_current_stage.png"
COMBO_IMAGE = r"assets\adb\combo.png"
ACTIVE_BOARD_IMAGE = r"assets\adb\active_board.png"
ADB_AUTO_FOLDER = r"assets\adb\auto"
# CONTINUE_IMAGE_IMAGE = r"assets\adb\continue_image.png"
# START_BUTTON_IMAGE = r"assets\adb\start_button.png"
# OK_BUTTON_IMAGE = r"assets\adb\ok_button.png"
# OK_BUTTON2_IMAGE = r"assets\adb\ok_button2.png"
# TO_MAP_BUTTON_IMAGE = r"assets\adb\to_map_button.png"

