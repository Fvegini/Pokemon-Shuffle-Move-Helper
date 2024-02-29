from pathlib import Path
from typing import List
from src import constants, custom_utils
from src.embed import loaded_embedder
import numpy as np

class Pokemon():
    def __init__(self, name, disabled, stage_added):
        self.name = name
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

    def __init__(self, path, barrier):
        if isinstance(path, str):
            path = Path(path)
        if path.stem == "_Fog":
            self.name = "Pikachu_a"
        elif path.stem == "_Empty":
            self.name = "Air"
        elif path.stem.startswith("_"):
            self.name = path.stem[1:]
        else:
            self.name = path.stem
        self.barrier = barrier
        self.barrier_type = ""
        self.original_path = path
        if self.barrier:
            self.name = f"{constants.BARRIER_PREFIX}{self.name}"
        self.populate_images()

    def __repr__(self):
        return self.name

    def populate_images(self):
        self.images_list = []
        if not self.barrier:
            directories = [constants.IMAGES_PATH, constants.IMAGES_EXTRA_PATH]
        else:
            directories = [constants.IMAGES_BARRIER_PATH]
            self.barrier_type = constants.BARRIER_TYPE_REAL
        matching_files = []
        for directory in directories:
            matching_files.extend(custom_utils.find_matching_files(directory, self.original_path.stem, ".*"))
            if len(matching_files) == 0:
                matching_files.extend(custom_utils.find_matching_files(directory, f"_{self.original_path.stem}", ".*"))
        for image_path in matching_files:
            image = custom_utils.open_and_resize_np_image(image_path, constants.downscale_res)
            self.images_list.append(CustomImage(image))


class Match():

    def __init__(self, board_icon, embed, icon: Icon):
        self.name = icon.name
        self.board_icon = board_icon
        cosine_tuples_list = [(loaded_embedder.cosine_similarity(embed, icon_image.embed), icon_image.image) for icon_image in icon.images_list]
        if len(cosine_tuples_list) > 0:
            self.cosine_similarity, self.match_icon = max(cosine_tuples_list, key=lambda x: x[0])
        else:
            self.cosine_similarity, self.match_icon = (0, None)

    def __repr__(self):
        return self.name

    def inspect_match(self):
        custom_utils.show_list_images([self.board_icon, self.match_icon])
        
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