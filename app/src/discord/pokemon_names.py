from src import constants, load_from_shuffle
from pathlib import Path
import os
from thefuzz import fuzz
from thefuzz import process

folder_path = constants.IMAGES_PATH

original_names_set = set([Path(f).stem for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))])

extra_names_dict = {
    "Zygarde-50": ["z50"],
    "Mega_Charizard_sx": ["smcx", "mega_charizard_x_shiny"],
    "Charizard_sx": ["mcx"],
}

for key in extra_names_dict:
    extra_names_dict[key] = [value.lower() for value in extra_names_dict[key]]
  

def find_original_key(search_value):
    global extra_names_dict
    search_value = search_value.lower()
    for key, values in extra_names_dict.items():
        if search_value in values:
            return key
    return None

def search_in_list_ignore_case(search_string, current_list=None):
    global original_names_set
    if not current_list:
        current_list = original_names_set
    search_string = search_string.lower()
    for item in current_list:
        if item.lower() == search_string:
            return item
    return None 

def create_shuffle_string_structure(line):
    try:
        line = line.lower()
        pokemons_list = []
        pokemons_not_found = {}
        mega = "-"
        for pokemon_name in line.split(","):
            pokemon_name.strip()
            final_pokemon_name = None
            pokemon_correct_name = None
            similar_name = None
            pokemon_name = pokemon_name.strip().replace(" ", "_")
            if search_in_list_ignore_case(pokemon_name, load_from_shuffle.exception_list):
                    pokemon_name = f"_{pokemon_name}"
            if pokemon_name in original_names_set:
                final_pokemon_name = pokemon_name
            elif (pokemon_correct_name := find_original_key(pokemon_name)):
                final_pokemon_name = pokemon_correct_name
            elif (pokemon_correct_name := search_in_list_ignore_case(pokemon_name)):
                final_pokemon_name = pokemon_correct_name
            else:
                similar_names = [fuzz_tuple[0] for fuzz_tuple in process.extractBests(pokemon_name, original_names_set, score_cutoff=80)]
                pokemons_not_found[pokemon_name] = similar_names
            if final_pokemon_name:
                if final_pokemon_name.startswith("Mega_"):
                    final_pokemon_name = final_pokemon_name.split("Mega_")[1]
                    mega = final_pokemon_name
                if final_pokemon_name not in pokemons_list:
                    pokemons_list.append(final_pokemon_name)
        if len(pokemons_list) > 0:
            final_string = f"STAGE NONE {','.join(pokemons_list)} {mega}"
        else:
            final_string = ""
        return final_string, pokemons_not_found
    except Exception as ex:
        print(f"Error on set team: {ex}")
        return "", {}
    
    
# string1 = "smcx, hoopa_u, tyranitar, hoopa u, hoopa unbound"

# create_shuffle_string_structure(string1)