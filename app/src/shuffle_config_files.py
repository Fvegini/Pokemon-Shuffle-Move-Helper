from pathlib import Path
from src import adb_utils, constants
from src import custom_utils
from src.discord import pokemon_names
from src.execution_variables import current_run
from src.classes import Pokemon, Board
import re

CROW = "false,false,false,false,false,false"
KEYS_LIST = ','.join(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
                    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'])
MEGA_NOT_ACTIVATED = "0"
MEGA_ACTIVATED = "99"

pattern = re.compile(r'^\d+(,\d+){2,}')

PREFERENCES_PATH = Path.joinpath(Path.home(), "Shuffle-Move", "config", "preferences.txt")
BOARD_PATH = Path.joinpath(Path.home(), "Shuffle-Move", "config", "boards", "board.txt")
TEAMS_DATA_PATH = Path.joinpath(Path.home(), "Shuffle-Move", "config", "teamsData.txt")
GRADING_MODES_PATH = Path.joinpath(Path.home(), "Shuffle-Move", "config", "gradingModes.txt")
STAGES_PATH = Path.joinpath(Path.home(), "Shuffle-Move", "config", "stages_mobile.txt")

stages_dict: dict[str, str] = {}
custom_utils.verify_shuffle_file(BOARD_PATH)
custom_utils.verify_shuffle_file(TEAMS_DATA_PATH)
custom_utils.verify_shuffle_file(GRADING_MODES_PATH)

def get_current_stage_and_team(expand_megas=False):

    stage_name = "NONE"
    with open(BOARD_PATH, 'r') as file:
        lines = file.readlines()
    for line in lines:
        if "STAGE" in line:
            stage_name = line.split(" ")[-1].strip()
            break
    return get_team_from_stage_name(stage_name, expand_megas), stage_name

def get_team_from_stage_name(stage_name, expand_megas=False):
    current_stage_string = f"TEAM {stage_name}"
    with open(TEAMS_DATA_PATH, 'r') as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        if line.lower().startswith(current_stage_string.lower()):
            return get_team_from_config_file_line(line.strip(), expand_megas)

def get_team_from_config_file_line(line, expand_megas):
    if line.startswith(("TEAM", "STAGE")):
        values_list = line.split()[2:]
    else:
        values_list = line.split()
    values_list = [item for item in values_list if not pattern.match(item)]
    if len(values_list) == 1 or values_list[1] == "-":
        current_team = values_list[0].split(",")
    else:
        current_team = values_list[0].split(",") + [f"Mega_{values_list[1]}"]
    if len(values_list) == 3:
        stage_added = values_list[2].split(",")
    else:
        stage_added = []
    final_team = []
    for pokemon_name in current_team:
        pokemon = Pokemon(pokemon_name, False, (pokemon_name in stage_added))
        if pokemon not in final_team:
            final_team.append(pokemon)
        mega_name = f"Mega_{pokemon.name}"
        if expand_megas:
            if mega_name in pokemon_names.original_names_set and mega_name not in final_team:
                final_team.append(Pokemon(mega_name, False, False))
    return final_team

def update_shuffle_move_files(current_board: Board, source=None, stage=None):
    names_list = []
    barrier_list = []
    mega_activated = MEGA_NOT_ACTIVATED
    mega_name = "-"

    for name in current_board.sequence_names_list:
        if "Barrier_" in name:
            name = name.split("Barrier_")[1]
            barrier_list.append("true")
        else:
            barrier_list.append("false")
        if "Mega_" in name:
            new_name = name.split("Mega_")[1]
            names_list.append(new_name)
            mega_activated = MEGA_ACTIVATED
            mega_name = new_name
        else:
            names_list.append(name)

    names_list, barrier_list, mega_name = process_pokemon_names_list(current_board.sequence_names_list)
    complete_names_list, _, forced_mega_name = process_pokemon_names_list(current_board.original_complete_names_list)
    current_board.barrier_list = barrier_list
    if mega_name == "-":
        mega_name = forced_mega_name
    else:
        mega_activated = MEGA_ACTIVATED
    current_board.mega_name = mega_name
    
    if custom_utils.is_survival_mode():
        stage = get_stage_name(current_board.stage_name)
    update_board_file(names_list, barrier_list, mega_activated, stage)
    update_preferences(current_board.current_score, current_board.moves_left)
    if current_run.has_modifications or source == "bot":
        update_teams_file(complete_names_list, mega_name, current_board.extra_supports_list, stage)
        update_gradingModes_file(source, mega_activated, current_board)
        current_run.has_modifications = False
    elif custom_utils.is_meowth_stage():
        update_gradingModes_file(source, mega_activated, current_board)
    elif current_run.current_strategy == constants.GRADING_MEGA_PROGRESS:
        update_gradingModes_file(source, mega_activated, current_board)
    has_mega = mega_activated == MEGA_ACTIVATED
    current_board.has_mega = has_mega
    return

def get_stage_name(stage_name):
    global stages_dict
    if len(stages_dict) == 0:
        stages_dict = load_stages_dict()
    exact_value = stages_dict.get(stage_name)
    if exact_value:
        return exact_value
    similar_key = custom_utils.find_similar_key(stage_name, stages_dict)
    if similar_key:
        return stages_dict.get(similar_key)
    else:
        return "NONE"

    

def load_stages_dict():
    stage_dict = {}
    with open(STAGES_PATH, 'r') as file:
        for line in file:
            if line.startswith('STAGE'):
                words = line.strip().split()
                if len(words) >= 3:
                    key, value = words[2], words[1]
                    stage_dict[key] = value
    return stage_dict

def process_pokemon_names_list(original_names_list):
    names_list = []
    barrier_list = []
    mega_name = "-"

    for name in original_names_list:
        if "Barrier_" in name:
            name = name.split("Barrier_")[1]
            barrier_list.append("true")
        else:
            barrier_list.append("false")
        if "Mega_" in name:
            new_name = name.split("Mega_")[1]
            names_list.append(new_name)
            mega_name = new_name
        else:
            names_list.append(name)    
    return names_list, barrier_list, mega_name

def update_current_stage(current_stage):
    with open(BOARD_PATH, 'r') as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        if line.startswith("STAGE"):
            # Replace the line
            lines[i] = f"STAGE {current_stage}\n"
            break
    with open(BOARD_PATH, 'w') as file:
        file.writelines(lines)
    return

def update_preferences(current_score=0, moves_left="5"):
    #INTEGER STAGE_CURRENT_SCORE 1111
    with open(PREFERENCES_PATH, 'r') as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        if line.startswith("INTEGER STAGE_CURRENT_SCORE"):
            # Replace the line
            lines[i] = f"INTEGER STAGE_CURRENT_SCORE {current_score}\n"
        if line.startswith("INTEGER STAGE_MOVES_REMAINING"):
            # Replace the line
            lines[i] = f"INTEGER STAGE_MOVES_REMAINING {moves_left}\n"
    with open(PREFERENCES_PATH, 'w') as file:
        file.writelines(lines)
    return 

def update_board_file(names_list, barrier_list, mega_activated, stage):
    if not stage:
        stage = current_run.current_stage
    board_file_content = f"""STAGE {stage}
MEGA_PROGRESS {mega_activated}
STATUS NONE
STATUS_DURATION 0
ROW_1 {",".join(names_list[0:6])}
FROW_1 {",".join(barrier_list[0:6])}
CROW_1 {CROW}
ROW_2 {",".join(names_list[6:12])}
FROW_2 {",".join(barrier_list[6:12])}
CROW_2 {CROW}
ROW_3 {",".join(names_list[12:18])}
FROW_3 {",".join(barrier_list[12:18])}
CROW_3 {CROW}
ROW_4 {",".join(names_list[18:24])}
FROW_4 {",".join(barrier_list[18:24])}
CROW_4 {CROW}
ROW_5 {",".join(names_list[24:30])}
FROW_5 {",".join(barrier_list[24:30])}
CROW_5 {CROW}
ROW_6 {",".join(names_list[30:36])}
FROW_6 {",".join(barrier_list[30:36])}
CROW_6 {CROW}
"""
    with open(BOARD_PATH, 'w') as file:
        file.write(board_file_content)

def update_teams_file_with_pokemon_list(pokemon_list, stage_name):
    names_list, _, mega_name = process_pokemon_names_list([pokemon.name for pokemon in pokemon_list])
    return update_teams_file(names_list, mega_name, [], stage_name)
    

def update_teams_file(names_list, mega_name, extra_supports_list, stage):
    if not stage:
        stage = current_run.current_stage
    move_string = f"TEAM {stage} {','.join(list(set(names_list)))} {KEYS_LIST} {mega_name} {','.join(list(set(extra_supports_list)))}\n"
    return update_teams_file_with_move_string(move_string, stage)

def update_teams_file_with_move_string(move_string, stage_name):
    team_stage_string = f"TEAM {stage_name}"
    with open(TEAMS_DATA_PATH, 'r') as file:
        lines = file.readlines()

    found = False
    # Find the line with the specified prefix
    for i, line in enumerate(lines):
        if line.startswith(team_stage_string):
            # Replace the line
            lines[i] = move_string
            found = True
            break
    if not found:
        lines.append(move_string)
    # Write the modified content back to the file
    with open(TEAMS_DATA_PATH, 'w') as file:
        file.writelines(lines)
    if custom_utils.custom_utils.is_survival_mode() and stage_name != constants.SURVIVAL_MODE_STAGE_NAME:
        new_stage_name = constants.SURVIVAL_MODE_STAGE_NAME
        new_move_string = move_string.replace(team_stage_string, f"TEAM {new_stage_name}")
        update_teams_file_with_move_string(new_move_string, new_stage_name)
    return move_string

def update_gradingModes_file(source, mega_activated, current_board):
    if source == "bot":
        strategy = constants.GRADING_TOTAL_SCORE
    elif custom_utils.is_meowth_stage():
        if current_board.moves_left.isnumeric() and int(current_board.moves_left) <= 2:
            strategy = '037MeowthEndGame'
        else:
            strategy = '037MeowthEarlyGame'
    else:
        strategy = current_run.current_strategy
    if strategy == constants.GRADING_MEGA_PROGRESS and mega_activated == MEGA_ACTIVATED:
        strategy = constants.GRADING_TOTAL_SCORE
    prefix_to_replace = f"STRING CURRENT_MODE"
    new_line = f"STRING CURRENT_MODE {strategy}\n"
    has_modifications = False
    with open(GRADING_MODES_PATH, 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        if line.startswith(prefix_to_replace):
            if lines[i] != new_line:
                lines[i] = new_line
                has_modifications = True
    if has_modifications:
        with open(GRADING_MODES_PATH, 'w') as file:
            file.writelines(lines)
    return