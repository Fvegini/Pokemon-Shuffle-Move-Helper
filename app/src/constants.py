from pathlib import Path


BARRIER_PREFIX = "Barrier_"
MEGA_PREFIX = "Mega_"

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
    "037MeowthEndGame": "037MeowthEndGame",
    "MegaBoostedScore": "MegaBoostedScore"
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
    "037": "STAGE 37",
    "SURVIVAL_MODE": "SURVIVAL MODE"
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
    },
    "1600x900": {
        "CompleteScreen": (0, 0, 900, 1600),
        "TopScreen": (0, 0, 900, 716),
        "HeartTimer": (44, 62, 158, 103),
        "Hearts": (230, 62, 299, 105),
        "Continue": (271, 1463, 646, 1578),
        "Start!": (271, 1463, 646, 1578),
        "To Map": (271, 1463, 646, 1578),
        "Next": (271, 1463, 646, 1578),
        "No": (153, 646, 742, 826),
        "No2": (681, 1040, 781, 1093), #This No appears when you click no start without hearts on a stage
        "NoOutOfTime": (646, 1343, 816, 1409), #Out of Time to Play
        "Yes": (153, 646, 742, 826),
        "StageMenu": (801, 27, 906, 162),
        "Combo": (602, 46, 813, 136),
        "CoinStage": (153, 646, 742, 826),
        "CoinStageYes": (118, 1041, 225, 1093),
        "Close": (348, 1033, 544, 1096),
        "Angry": (70, 686, 826, 915), #The Grey Angry! text
        # "EscalationLevel": (558, 434, 841, 623),
        "Pokeball Capture": (320, 1028, 577, 1272),
        "Greatball": (110, 1259, 803, 1308), #Do you want to use 3500 Coins
        "GreatballNo": (691, 1453, 772, 1509),
        "GreatballYes": (123, 1460, 217, 1506),
        # Stage
        "Board": (16, 716, 886, 1586),
        "Stage": (34, 87, 202, 125),
        "StageName": (581, 546, 890, 586),
        "Score": (32, 187, 200, 222),
        "MovesLeft": (39, 551, 240, 620),
    }
}

SURVIVAL_MODE_STAGE_NAME = "SURVIVAL_MODE"

SURVIVAL_MODE_TXT = r"assets\survival_list.txt"
ADB_IMAGE_FOLDER = r"assets\adb"
MEOWTH_DEBUG_IMAGE_FOLDER = r"debug\meowth"
DEBUG_STAGES_IMAGE_FOLDER = r"debug\complete"
DEBUG_EXTRA_IMAGE_FOLDER = r"debug\extra"
CURRENT_STAGE_IMAGE = r"assets\adb\current_stage.png"
MEOWTH_STAGE_IMAGE = r"assets\adb\meowth_037.png"
SURVIVAL_MODE_STAGE_IMAGE = r"assets\adb\survival_mode.png"
INFO_ICON_IMAGE = r"assets\adb\info_icon.png"
COMBO_IMAGE = r"assets\adb\combo.png"
ACTIVE_BOARD_IMAGE = r"assets\adb\active_board.png"
OK_BUTTON_IMAGE = r"assets\adb\ok_button.png"
OK_BUTTON2_IMAGE = r"assets\adb\ok_button2.png"
RETURN_FLAG_IMAGE = r"assets\adb\return_flag1.png"
RETURN_FLAG2_IMAGE = r"assets\adb\return_flag2.png"
ANGRY_ICON_IMAGE = r"assets\adb\angry_1.png"
ANGRY_ICON2_IMAGE = r"assets\adb\angry_2.png"
POKEBALL_CAPTURE_IMAGE = r"assets\adb\pokeball_capture.png" 
