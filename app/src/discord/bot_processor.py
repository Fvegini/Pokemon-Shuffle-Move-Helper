import cv2
import numpy as np
import math
from src import custom_utils, load_from_shuffle, shuffle_config_files, match_icons, config_utils, constants
import requests
import pickle
from src.classes import Pokemon
from src.discord import pokemon_names
import asyncio
from io import BytesIO
import discord

known_scales_dict = {
    (750 / 1334): (7 / 1334), #Felipe Phone
    (591 / 1280): (57 / 1280), #Gabriel Phone
    (1080 / 2400): (135 / 2400), #Internet Phone
    (608 / 1200): (6 / 1200), #Internet Phone
}

square_size_percentage = (730 / 750)
scaled_square_size_starting_point_percentage = (10 / 750)

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


async def process_with_image_url(ctx, url, target_user=None):
    try:
        original_image = load_image_cv2(url)
        cropped_image = get_cropped_image(original_image)
        current_team, current_stage =  shuffle_config_files.get_current_stage_and_team(expand_megas=True)
        if current_team is None and current_stage is None:
            return await send_message(ctx, "You must Select a Team First", target_user)
        elif current_team is None and current_stage:
            return await send_message(ctx, f"The Selected stage {current_stage} don't have any pokemon selected", target_user)
        if "Wood" not in current_team:
            current_team.append(Pokemon("Wood", False, False))
        if "Metal" not in current_team:
            current_team.append(Pokemon("Metal", False, False))
        if "Air" not in current_team:
            current_team.append(Pokemon("Air", False, False))

        result, final_image = match_icons.start_from_bot(current_team, True, cropped_image, current_stage, create_image=True)

        image_bytes = cv2.imencode('.png', final_image)[1].tobytes()
        image_file = BytesIO(image_bytes)
        if ctx.message.author.name == "WebhookTest" and target_user:
            await ctx.send(file=discord.File(image_file, "final_image.png"))
            await target_user.send(result)
        else:
            await ctx.send(file=discord.File(image_file, "final_image.png"))
            await ctx.send(f"Result: {result}")
    except Exception as ex:
        send_message(ctx, str(ex), target_user)
    

async def show_team(ctx):
    team_list, _ =  shuffle_config_files.get_current_stage_and_team()
    await send_message(ctx, f"{team_list}")

async def add_to_team(ctx, pokemon_name):
    try:
        team_list, stage_name =  shuffle_config_files.get_current_stage_and_team()
        pokemon = pokemon_names.find_pokemon(pokemon_name)
        if pokemon in team_list:
            await send_message(ctx, f"{pokemon} was already on team {stage_name}")
        else:
            team_list.append(pokemon)
            final_shuffle_string = shuffle_config_files.update_teams_file_with_pokemon_list(team_list, stage_name)
            if final_shuffle_string:
                await send_message(ctx, f"Successfully added {pokemon} to the team {stage_name}")
    except Exception as ex:
        await send_message(ctx, ex)

async def remove_from_team(ctx, pokemon_name):
    try:
        team_list, stage_name =  shuffle_config_files.get_current_stage_and_team()
        pokemon = pokemon_names.find_pokemon(pokemon_name)
        if pokemon not in team_list:
            await send_message(ctx, f"{pokemon} isn't on {stage_name}")
        else:
            team_list.remove(pokemon)
            final_shuffle_string = shuffle_config_files.update_teams_file_with_pokemon_list(team_list, stage_name)
            if final_shuffle_string:
                await send_message(ctx, f"Successfully removed {pokemon} from the team {stage_name}")
    except Exception as ex:
        await send_message(ctx, ex)

async def set_team_stage(ctx, team_text):
    global user_teams_dict
    if team_text.strip().upper() in load_from_shuffle.stages_set:
        stage_name = team_text.strip().upper()
        current_team = shuffle_config_files.get_team_from_stage_name(stage_name, expand_megas=True)
        team_string = f"STAGE {stage_name} {','.join([pokemon.name for pokemon in current_team])}"
        # pokemons_not_found = []
        shuffle_config_files.update_current_stage(stage_name)
        await send_message(ctx, f"Team registered: {current_team}")
    else:
        await send_message(ctx, f"Not Found a Team with the name: {team_text.strip().upper()}")
        await send_message(ctx, f"Possible teams are: {load_from_shuffle.stages_set}")

async def send_message(ctx, message, target_user=None):
    if ctx and target_user:
        await target_user.send(message)
    elif ctx:
        await ctx.send(message)
    else:
        print(message)

if __name__ == "__main__":
    # result = process_with_image_url(r"https://media.discordapp.net/attachments/1205125025062060042/1207083761649586298/IMG_3916.png?ex=65de5b5b&is=65cbe65b&hm=44cde4e9112f20b54c220bdfcea14d4de008fa3a5cc4abc47fabea94c20b234c&=&format=webp&quality=lossless", None)
    # print(result)
    asyncio.run(set_team_stage("fire", None))