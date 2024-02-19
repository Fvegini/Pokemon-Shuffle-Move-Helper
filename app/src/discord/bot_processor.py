import cv2
import numpy as np
import math
from src import custom_utils, load_from_shuffle, shuffle_config_files, match_icons, config_utils, constants
import requests
import pickle
from src.discord import pokemon_names
import asyncio

USER_TEAMS_PKL = "user_teams.pkl"

try:
    with open(USER_TEAMS_PKL, 'rb') as file:
        user_teams_dict = pickle.load(file)
except:
    user_teams_dict = {}

known_scales_dict = {
    (750 / 1334): (7 / 1334), #Felipe Phone
    (591 / 1280): (57 / 1280), #Gabriel Phone
    (1080 / 2400): (135 / 2400), #Internet Phone
    (608 / 1200): (6 / 1200), #Internet Phone
}

square_size_percentage = (730 / 750)
scaled_square_size_starting_point_percentage = (10 / 750)

def update_teams_pkl():
    global user_teams_dict
    with open(USER_TEAMS_PKL, 'wb') as file: 
        pickle.dump(user_teams_dict, file) 

def closest_number(number_to_compare, number_list):
     
    closest = number_list[min(range(len(number_list)), key = lambda i: abs(number_list[i]-number_to_compare))]
    
    if math.isclose(closest, number_to_compare, abs_tol=0.01):
        return closest, True
    else:
        return closest, False

def get_cropped_image(img):
    image_scale = img.shape[1] / img.shape[0]
    closest_scale_number, was_really_close = closest_number(image_scale, list(known_scales_dict.keys()))
    if was_really_close:
        offset_scale = known_scales_dict.get(closest_scale_number)
    else:
        offset_scale = known_scales_dict.get(closest_scale_number)
        print(f"New Scale Found, using the closest - {offset_scale}")
        print(f"Image dimensions were: {img.shape}")

    offset = img.shape[0] * offset_scale
    width = int(img.shape[1] * square_size_percentage)
    height = int(img.shape[1] * square_size_percentage)
    start_x = int(img.shape[1] * scaled_square_size_starting_point_percentage)
    start_y = int(img.shape[0] - width - offset)

    return img[start_y:start_y+height, start_x:start_x+width]

    # cv2.imwrite("croped.jpg" ,cropped_img) 

    # cv2.rectangle(img, (start_x, start_y), (start_x+width, start_y+height), (0, 0, 255), 2)

    # cell_size = width / 6
    # for y in range(0, 6):
    #     for x in range(0, 6):
    #         cell_box_x = (int(start_x + x*cell_size), int(start_y + y*cell_size))
    #         cell_box_y = (int(start_x + (x+1)*cell_size), int(start_y + (y+1)*cell_size))
    #         cv2.rectangle(img, cell_box_x, cell_box_y, (0, 0, 255), 2)
    
    
def load_image_cv2(url):
    response = requests.get(url)
    img_array = np.array(bytearray(response.content), dtype=np.uint8)
    img_cv2 = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return img_cv2


async def process_with_image_url(url, ctx, username="Vegini", text=""):
    original_image = load_image_cv2(url)
    cropped_image = get_cropped_image(original_image)
    if text:
        await register_team(username, text, ctx)

    current_team = load_team(username)
    result = match_icons.start_from_bot(current_team, True, cropped_image)
    try:
       red = result.split(":")[0].split("->")[0].strip()
       blue = result.split(":")[0].split("->")[1].strip()
    except:
        red = None
        blue = None
    splitted_image = custom_utils.make_cell_list_from_img(cropped_image, True, red, blue)
    final_image = custom_utils.concatenate_cv2_images(splitted_image)
    return result, final_image
    

def load_team(username):
    global user_teams_dict
    team_text = user_teams_dict.get(username)
    final_team = shuffle_config_files.get_team_from_teams_data_line(team_text, expand_megas=True)
    return final_team

async def show_team(username, ctx):
    global user_teams_dict
    team_string =  user_teams_dict.get(username)
    await ctx.send(f"Team registered: {shuffle_move_team_string_format(team_string)}")

def shuffle_move_team_string_format(original_line):
    text = original_line.replace('STAGE NONE','').strip()
    text_list = text.split(" ")
    if len(text_list) == 1 or text_list[1] == "-":
        return f'{", ".join(text_list[0].split(","))}'
    else:
        return f'{", ".join(text_list[0].split(","))}, Mega_{text_list[1]}'

async def register_team(username, team_text, ctx):
    global user_teams_dict
    if team_text.strip().upper() in load_from_shuffle.stages_set:
        stage_name = team_text.strip().upper()
        current_team = shuffle_config_files.get_team_from_stage_name(stage_name, expand_megas=True)
        team_string = f"STAGE NONE {','.join([pokemon.name for pokemon in current_team])}"
        pokemons_not_found = []
        # current_team, current_stage = shuffle_config_files.get_current_stage_and_team()
        # shuffle_config_files.update_teams_file_with_move_string(complete_names_list, mega_name, "NONE")
    else:
        team_string, pokemons_not_found = pokemon_names.create_shuffle_string_structure(team_text, expand_megas=True)
    if len(pokemons_not_found) > 0:
        for key in pokemons_not_found:
            await ctx.send(f"{key} not found, similar names found: {pokemons_not_found.get(key)}")
    if team_string != "":
        user_teams_dict[username] = team_string
        update_teams_pkl()
        await ctx.send(f"Team registered: {shuffle_move_team_string_format(team_string)}")
        return True
    else:
        await ctx.send(f"Team Not Registered.")


if __name__ == "__main__":
    # result = process_with_image_url(r"https://media.discordapp.net/attachments/1205125025062060042/1207083761649586298/IMG_3916.png?ex=65de5b5b&is=65cbe65b&hm=44cde4e9112f20b54c220bdfcea14d4de008fa3a5cc4abc47fabea94c20b234c&=&format=webp&quality=lossless", None)
    # print(result)
    asyncio.run(register_team("Vegini", "latest fire", None))