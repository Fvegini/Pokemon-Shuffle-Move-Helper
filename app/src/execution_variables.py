from pathlib import Path
from src import classes, log_utils

log = log_utils.get_logger()
class ExecutionVariable:
    
    current_stage: str
    current_strategy: str
    
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
        self.metal_icon = classes.Icon("Metal", Path("Metal.png"), False)
        self.metal_match = classes.Match(None, None, self.metal_icon)
        self.is_combo_active = False
        self.id = None
        self.first_move = False
        self.move_number = 0

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


current_run = ExecutionVariable()