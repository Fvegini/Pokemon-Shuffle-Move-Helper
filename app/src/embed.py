import mediapipe as mp
import glob
from pathlib import Path

BaseOptions = mp.tasks.BaseOptions
ImageEmbedder = mp.tasks.vision.ImageEmbedder
ImageEmbedderOptions = mp.tasks.vision.ImageEmbedderOptions
VisionRunningMode = mp.tasks.vision.RunningMode

model_path = Path(r"models\1.tflite")

class Embedder():
    
    def __init__(self, model_path=model_path):
        model_path = Path(model_path)
        options = ImageEmbedderOptions(
	    	base_options=BaseOptions(model_asset_path=model_path),
		    quantize=False,
		    running_mode=VisionRunningMode.IMAGE)

        self.embedder = ImageEmbedder.create_from_options(options)
    
    def create_embed_from_np(self, numpy_image):
        return self.embedder.embed(mp.Image(image_format=mp.ImageFormat.SRGB, data=numpy_image)).embeddings[0]
    
    def create_embed_from_path(self, image_path):
        return self.embedder.embed(mp.Image.create_from_file(image_path.as_posix())).embeddings[0]
    
    def cosine_similarity(self, embed_1, embed_2):
        return ImageEmbedder.cosine_similarity(embed_1, embed_2)
