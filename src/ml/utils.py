import typing as t

import orjson
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

def save_json_with_arrays(
    dict_with_arrays: t.Dict[str, NDArray[float]],
    save_path: str,
) -> None:
    dict_with_arrays_serializable = {key: value.tolist() for key, value in tqdm(dict_with_arrays.items(), desc='convering np.arrays to lists')}
    with open(save_path, mode='wb') as f:
        f.write(orjson.dumps(dict_with_arrays_serializable))
    return


def encode_images(
    images_urls: t.Dict[int, str],
    encoder_model: ImageEncoder,
    verbose: bool=False,
    save_every_n_iterations: t.Optional[int]=None,
    save_path: t.Optional[str]=None
) -> t.Dict[str, t.Dict[int, NDArray[float]]]:
    images_embeddings_dict = {}
    for i, (item_id, images_list) in (tqdm(enumerate(images_urls.items(), start=1)) if verbose else enumerate(images_urls.items(), start=1)):
        try:
            if item_id not in images_embeddings_dict:
                images_embeddings_dict[item_id] = {}
            for image_url in images_list:
                image_number = int(image_url.split("/")[-1].replace('.webp', ''))
                images_embeddings_dict[item_id][image_number] = encoder_model.encode(image_url=image_url)
            if save_every_n_iterations is not None and save_path is not None:
                if i % save_every_n_iterations == 0:
                    dict_with_arrays_serializable = {str(key): {str(k_): value.tolist() for k_, value in subdict.items()} for key, subdict in tqdm(images_embeddings_dict.items(), desc='convering np.arrays to lists')}
                    if verbose: print("\nsaving intermediate images_embeddings_dict to disc...")
                    with open(save_path, mode='wb') as f:
                        f.write(orjson.dumps(dict_with_arrays_serializable))
                    if verbose: print("\nsaving intermediate images_embeddings_dict to disc ✔")
        except Exception as e:
            print(f"Exception raised when trying to encode image at iteration {i}!")
            print(e, end='\n')
    return images_embeddings_dict