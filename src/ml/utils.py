import typing as t

from tqdm import tqdm
import requests
from numpy.typing import NDArray
from transformers import ViTImageProcessor, ViTModel
from PIL import Image
from PIL.WebPImagePlugin import WebPImageFile

class ImageEncoder:
    def __init__(self, model_str: str='google/vit-base-patch16-224-in21k'):
        print("initializing ImageEncoder...")
        self.processor = ViTImageProcessor.from_pretrained(model_str)
        self.model = ViTModel.from_pretrained(model_str)
        print("ok")
        
    @staticmethod
    def _get_image_file_from_url(image_url: str) -> WebPImageFile:
        image = Image.open(requests.get(image_url, stream=True).raw).convert("RGB")
        return image
        
    def encode(self, image_url: str) -> NDArray[float]:
        image = ImageEncoder._get_image_file_from_url(image_url=image_url)
        inputs = self.processor(images=image, return_tensors="pt")
        outputs = self.model(**inputs)
        image_emb = outputs.last_hidden_state[0][0].detach().numpy()
        return image_emb    



def encode_images(
    images_urls: t.Dict[int, str],
    encoder_model: ImageEncoder,
    verbose: bool=False
) -> t.Dict[str, t.Dict[int, NDArray[float]]]:
    images_embeddings_dict = {}
    for item_id, images_list in (tqdm(images_urls.items()) if verbose else images_urls.items()):
        if item_id not in images_embeddings_dict:
            images_embeddings_dict[item_id] = {}
        for image_url in images_list:
            image_number = int(image_url.split("/")[-1].replace('.webp', ''))
            images_embeddings_dict[item_id][image_number] = encoder_model.encode(image_url=image_url)
    return images_embeddings_dict