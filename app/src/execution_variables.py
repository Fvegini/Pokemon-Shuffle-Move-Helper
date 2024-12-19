from pathlib import Path
from src import classes, constants, log_utils
from adbutils import AdbDevice
from typing import Optional
from datetime import datetime

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import ImageSelectorApp

log = log_utils.get_logger()
class ExecutionVariable:
    
    current_stage: str
    current_strategy: str
    root: "ImageSelectorApp" = None #type:ignore
    adb_device: Optional[AdbDevice]

    def __init__(self):
        self.current_stage = ""
        self.current_strategy = ""
        self.has_modifications = True
        self.socket_mode = True
        self.non_stage_count = 0
        self.hearts_loop_counter = 0
        self.adb_shell_command = "adb shell"
        self.angry_mode_active = False
        self.last_stage_had_anger = False
        self.thread_sleep_timer = 0
        self.stage_timer = None
        self.last_swipe_timer = None
        self.mega_activated_this_round = False
        self.last_execution_swiped = False
        self.last_pokemon_board_sequence = None
        self.metal_icon = classes.Icon("Metal", Path("Metal.png"), False, True)
        self.metal_match = classes.Match(None, None, self.metal_icon)
        self.is_combo_active = False
        self.id = None
        self.first_move = False
        self.move_number = 0
        self.fake_matches: list[classes.Match] = []
        self.current_fake_match_index = -1
        self.auto_disabled_count = 0
        self.disable_loop = False
        self.awakened_from_sleep = False
        self.awakened_expected_counter = 0
        self.bad_board_count = 0
        self.has_drops = False
        self.abd_not_found_count = 0
        self.is_loop_active = False
        self.survival_mode_current_stage = 0
        self.survival_mode_current_stage_name = ""
        self.survival_mode_current_running = False
        self.survival_mode_run_started_time = datetime.now()
        self.survival_mode_current_stage_started = datetime.now()
        self.survival_mode_current_stage_loop_count = 0
        self.survival_old_stage_info = {}
        self.survival_current_stage_info = {}
        self.survival_mode_current_running_path = None
        self.survival_mode_current_id = datetime.now()
        self.survival_mode_current_team = ""

    def clear_survival_variables(self):
        self.survival_mode_current_stage_loop_count = 0
        self.survival_mode_current_stage = 0
        self.survival_mode_current_stage_name = ""
        self.survival_mode_current_running = False
        self.survival_mode_run_started_time = datetime.now()
        self.survival_mode_current_stage_started = datetime.now()
        self.survival_old_stage_info = {}
        self.survival_current_stage_info = {}
        self.survival_mode_current_running_path = None
        self.survival_mode_current_id = datetime.now()

    def clear_stage_variables(self):
        if self.angry_mode_active:
            log.warning("ANGRY MODE IS BEING DEACTIVATED BY CLEAR_STAGE_VARIABLES")
        if self.last_stage_had_anger:
            log.warning("CLEAR VARIABLES WAS ACTIVATED WHILE THE last_stage_had_anger VARIABLE WAS ON")
        self.last_swipe_timer = None
        self.last_pokemon_board_sequence = None
        self.is_combo_active = False
        self.mega_activated_this_round = False
        self.last_execution_swiped = False
        self.stage_timer = None
        self.id = None
        self.move_number = 0
        self.first_move = False
        self.angry_mode_active = False
        self.hearts_loop_counter = 0
        self.non_stage_count = 0
        self.awakened_from_sleep = False
        self.auto_disabled_count = 0
        self.bad_board_count = 0
        self.awakened_expected_counter = 0
        self.has_drops = False
        self.abd_not_found_count = 0
        self.survival_mode_current_stage_loop_count = 0
        
    def load_fake_matchs(self, original_icons, keep_current_stage_add=False):
        log.info("RUNNING THE LOAD_FAKE_MATCHS LOGIC")
        for image_path in Path(constants.IMAGES_PATH).glob("*.png"):
            if image_path.stem not in original_icons:
                icon = classes.Icon(image_path.stem, image_path, False, True)
                match = classes.Match(None, None, icon)
                self.fake_matches.append(match)
                if len(self.fake_matches) > 15:
                    return
        
    def get_next_timed_fake_icon(self):
        if len(self.fake_matches) == 0:
            self.load_fake_matchs([])
        self.current_fake_match_index = (self.current_fake_match_index + 1) % len(self.fake_matches)
        return self.fake_matches[self.current_fake_match_index]


current_run = ExecutionVariable()