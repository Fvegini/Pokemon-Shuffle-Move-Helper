from pathlib import Path
from typing import List
from src import constants, file_utils
from src.embed import loaded_embedder
import numpy as np

class Pokemon():
    def __init__(self, name, disabled, stage_added):
        path = Path(name)
        self.name = path.stem
        if not path.suffix:
            self.path = path.with_suffix(".png")
        else:
            self.path = path
        self.disabled = disabled
        self.stage_added = stage_added
        
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

class CustomImage():

    def __init__(self, image):
        self.image = image
        self.embed = loaded_embedder.create_embed_from_np(image)

class Icon():

    name: str
    barrier: bool
    barrier_type: str
    original_path: Path
    images_list: List[CustomImage]

    def __init__(self, name, path, barrier):
        if name == "_Empty":
            self.name = "Air"
        elif name.startswith("_"):
            self.name = path.stem[1:]
        else:
            self.name = name
        self.barrier = barrier
        self.barrier_type = ""
        self.original_path = path
        if self.barrier:
            self.name = f"{constants.BARRIER_PREFIX}{self.name}"
        self.populate_images()

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    def populate_images(self):
        self.images_list = []
        if not self.barrier:
            directories = [constants.IMAGES_PATH, constants.IMAGES_EXTRA_PATH]
        else:
            directories = [constants.IMAGES_BARRIER_PATH]
            self.barrier_type = constants.BARRIER_TYPE_REAL
        matching_files = []
        for directory in directories:
            matching_files.extend(file_utils.find_matching_files(directory, self.original_path.stem, ".*"))
            if len(matching_files) == 0:
                matching_files.extend(file_utils.find_matching_files(directory, f"_{self.original_path.stem}", ".*"))
        for image_path in matching_files:
            image = file_utils.open_and_resize_np_image(image_path, constants.downscale_res)
            self.images_list.append(CustomImage(image))


class Match():

    def __init__(self, board_icon, embed, icon: Icon):
        self.name = icon.name
        self.board_icon = board_icon
        cosine_tuples_list = []
        try:
            cosine_tuples_list = [(loaded_embedder.cosine_similarity(embed, icon_image.embed), icon_image.image) for icon_image in icon.images_list]
        except:
            pass
        if len(cosine_tuples_list) > 0:
            self.cosine_similarity, self.match_icon = max(cosine_tuples_list, key=lambda x: x[0])
        else:
            self.cosine_similarity, self.match_icon = (0, None)

    def __repr__(self):
        return f"{self.name} - {self.cosine_similarity}"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    def inspect_match(self):
        file_utils.show_list_images([self.board_icon, self.match_icon])
        
class MatchResult():
    
    result: str
    match_list: List[Match]
    match_image: np.ndarray
    
    def __init__(self, result="", match_list=None, match_image=None):
        self.result = result
        self.match_list = match_list
        self.match_image = match_image
        
    def __repr__(self):
        return self.result

    def __bool__(self):
        return bool(self.result)

class Board():
    
    match_sequence: List[Match]
    pokemon_board_sequence: List[str]
    extra_supports_list: list[str]
    sequence_names_list: list[str]
    original_complete_names_list: list[str]
    frozen_list: list[str]
    has_mega: bool
    mega_name: str
    moves_left: str = "5"
    current_score: int = 0
    stage_name: str = ""
    
    def __init__(self, match_sequence: List[Match], pokemon_list: List[Pokemon], icons_list: List[Icon]):
        self.match_sequence = match_sequence
        self.extra_supports_list = [pokemon.name for pokemon in pokemon_list if pokemon.stage_added]
        self.sequence_names_list = [match.name for match in self.match_sequence]
        self.original_complete_names_list = [icon.name for icon in icons_list]
        self.pokemon_board_sequence = [match.name for match in self.match_sequence]
        self.frozen_list = []
        self.has_mega = False

class Screen():
    
    loaded: bool = True
    resolution_dict: dict
    board_top_left: tuple
    board_bottom_right: tuple
    board_x: int
    board_y: int
    board_w: float
    board_h: float
    
    def __init__(self, resolution_dict={}):
        self.mydict = resolution_dict
        board = resolution_dict.get("Board")
        if not board:
            self.loaded = False
            board = (0, 0, 0, 0)
        board_top_left = board[0:2]
        board_bottom_right = board[2:4]
        self.board_top_left = board_top_left
        self.board_bottom_right = board_bottom_right
        self.board_x = board_top_left[0]
        self.board_y = board_top_left[1]
        self.board_w = (board_bottom_right[0] - board_top_left[0]) / 6
        self.board_h = (board_bottom_right[1] - board_top_left[1]) / 6
    
    def get_position(self, position):
        return self.mydict.get(position)