from pathlib import Path
from src import classes

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
        self.thread_sleep_timer = 0
        self.stage_timer = None
        self.mega_activated_this_round = False
        self.last_execution_swiped = False
        self.last_pokemon_board_sequence = None
        self.metal_icon = classes.Icon("Metal", Path("Metal.png"), False)
        self.metal_match = classes.Match(None, None, self.metal_icon)
        self.is_combo_active = False
        

current_run = ExecutionVariable()