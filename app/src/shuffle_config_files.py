from pathlib import Path
from src import constants
from src.discord import pokemon_names
from src.execution_variables import execution_variables
from src.classes import Pokemon
import re

CROW = "false,false,false,false,false,false"
KEYS_LIST = ','.join(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
                    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'])
MEGA_NOT_ACTIVATED = "0"
MEGA_ACTIVATED = "99"

pattern = re.compile(r'^\d+(,\d+){2,}')
BOARD_PATH = Path.joinpath(Path.home(), "Shuffle-Move", "config", "boards", "board.txt")
TEAMS_DATA_PATH = Path.joinpath(Path.home(), "Shuffle-Move", "config", "teamsData.txt")
GRADING_MODES_PATH = Path.joinpath(Path.home(), "Shuffle-Move", "config", "gradingModes.txt")

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

def create_board_files(sequence_names_list, original_complete_names_list, extra_supports_list, source=None, stage=None):
    names_list = []
    frozen_list = []
    mega_activated = MEGA_NOT_ACTIVATED
    mega_name = "-"

    for name in sequence_names_list:
        if "Barrier_" in name:
            name = name.split("Barrier_")[1]
            frozen_list.append("true")
        else:
            frozen_list.append("false")
        if "Mega_" in name:
            new_name = name.split("Mega_")[1]
            names_list.append(new_name)
            mega_activated = MEGA_ACTIVATED
            mega_name = new_name
        else:
            names_list.append(name)

    names_list, frozen_list, mega_name = process_pokemon_names_list(sequence_names_list)
    complete_names_list, _, forced_mega_name = process_pokemon_names_list(original_complete_names_list)
    if mega_name == "-":
        mega_name = forced_mega_name
    else:
        mega_activated = MEGA_ACTIVATED

    update_board_file(names_list, frozen_list, mega_activated, stage)
    if execution_variables.has_modifications or source == "bot":
        update_teams_file(complete_names_list, mega_name, extra_supports_list, stage)
        update_gradingModes_file(source, mega_activated)
        execution_variables.has_modifications = False
    elif execution_variables.current_strategy == constants.GRADING_MEGA_PROGRESS:
        update_gradingModes_file(source, mega_activated)
    return

def process_pokemon_names_list(original_names_list):
    names_list = []
    frozen_list = []
    mega_name = "-"

    for name in original_names_list:
        if "Barrier_" in name:
            name = name.split("Barrier_")[1]
            frozen_list.append("true")
        else:
            frozen_list.append("false")
        if "Mega_" in name:
            new_name = name.split("Mega_")[1]
            names_list.append(new_name)
            mega_name = new_name
        else:
            names_list.append(name)    
    return names_list, frozen_list, mega_name

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

def update_board_file(names_list, frozen_list, mega_activated, stage):
    if not stage:
        stage = execution_variables.current_stage
    board_file_content = f"""STAGE {stage}
MEGA_PROGRESS {mega_activated}
STATUS NONE
STATUS_DURATION 0
ROW_1 {",".join(names_list[0:6])}
FROW_1 {",".join(frozen_list[0:6])}
CROW_1 {CROW}
ROW_2 {",".join(names_list[6:12])}
FROW_2 {",".join(frozen_list[6:12])}
CROW_2 {CROW}
ROW_3 {",".join(names_list[12:18])}
FROW_3 {",".join(frozen_list[12:18])}
CROW_3 {CROW}
ROW_4 {",".join(names_list[18:24])}
FROW_4 {",".join(frozen_list[18:24])}
CROW_4 {CROW}
ROW_5 {",".join(names_list[24:30])}
FROW_5 {",".join(frozen_list[24:30])}
CROW_5 {CROW}
ROW_6 {",".join(names_list[30:36])}
FROW_6 {",".join(frozen_list[30:36])}
CROW_6 {CROW}
"""
    with open(BOARD_PATH, 'w') as file:
        file.write(board_file_content)

def verify_shuffle_file(file_path: Path):
    if not file_path.exists():
        print(f"File {file_path.as_posix()} not found")

def update_teams_file_with_pokemon_list(pokemon_list, stage_name):
    names_list, _, mega_name = process_pokemon_names_list([pokemon.name for pokemon in pokemon_list])
    return update_teams_file(names_list, mega_name, [], stage_name)
    

def update_teams_file(names_list, mega_name, extra_supports_list, stage):
    if not stage:
        stage = execution_variables.current_stage
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
        lines[-1] = move_string
    # Write the modified content back to the file
    with open(TEAMS_DATA_PATH, 'w') as file:
        file.writelines(lines)
    return move_string

def update_gradingModes_file(source, mega_activated):
    if source == "bot":
        strategy = constants.GRADING_TOTAL_SCORE
    else:
        strategy = execution_variables.current_strategy
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

verify_shuffle_file(BOARD_PATH)
verify_shuffle_file(TEAMS_DATA_PATH)
verify_shuffle_file(GRADING_MODES_PATH)