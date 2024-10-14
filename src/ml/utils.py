from pickle import FALSE
import typing as t

import orjson
from tqdm import tqdm
import requests
import torch
from numpy.typing import NDArray
from transformers import ViTImageProcessor, ViTModel
from PIL import Image
from PIL.Image import Image as ImageType
from PIL.WebPImagePlugin import WebPImageFile

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from src.utils import show_items_images


ItemPayloadDataType = t.Dict[str, t.Any]


def _get_image_file_from_url(image_url: str) -> WebPImageFile:
    image = Image.open(requests.get(image_url, stream=True).raw).convert("RGB")
    return image
    
def get_device() -> str:
  return 'cuda' if torch.cuda.is_available() else 'cpu'


class ImageEncoder:
    def __init__(self, model_str: str='google/vit-base-patch16-224-in21k', device: str='cpu'):
        self.device = device      
        print(f"initializing ImageEncoder on device={device}...")
        self.processor = ViTImageProcessor.from_pretrained(model_str)
        self.model = ViTModel.from_pretrained(model_str).to(self.device)
        print("ok")
        
    def encode(self, image_url: t.Optional[str]=None, image: t.Optional[ImageType]=None) -> NDArray[float]:
        assert (
            (int(image_url is not None) + int(image is not None)) % 2 != 0,
            "At least one (and maximum one!) of image_url or image should be provided!"
        )
        if image is None:
            # image = ImageEncoder._get_image_file_from_url(image_url=image_url)
            image = _get_image_file_from_url(image_url=image_url)
        with torch.no_grad():
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            outputs = self.model(**inputs)
            image_emb = outputs.last_hidden_state[0][0].to('cpu').detach().numpy()
        return image_emb 

    @staticmethod
    def batchify_image_urls(images_urls: t.List[str], verbose: bool=False) -> t.List[ImageType]:
      images = []
      for url in (tqdm(images_urls, desc='batching images') if verbose else images_urls):
          image = Image.open(requests.get(url, stream=True).raw).convert("RGB")
          images.append(image)
      return images
      

    def encode_batch(
      self, 
      images_urls: t.Optional[t.List[str]]=None, 
      images: t.Optional[t.List[ImageType]]=None,
      verbose: bool=False,
    ) -> NDArray[float]:
      assert (
          (int(images_urls is not None) + int(images is not None)) % 2 != 0,
          "At least one (and maximum one!) of image_url or image should be provided!"
      )
      if images is None:
        images_batch = self.batchify_image_urls(images_urls=images_urls, verbose=verbose)
      else:
        images_batch = images
      # Preprocess images and convert to tensors
      inputs = self.processor(images=images_batch, return_tensors="pt", padding=True)
      # Encode the images
      with torch.no_grad():  # Disable gradient calculation for inference
          outputs = self.model(**inputs.to(self.device))
      # Get the last hidden states
      last_hidden_states = outputs.last_hidden_state
      # If you want to get the embeddings for each image
      embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()  # Take the [CLS] token representation
      return embeddings
 
      

class VectorIndex:
    def __init__(self, url: str, index_name: str):
        self.index = QdrantClient(url)
        self.index_name = index_name
        
    def _init_index(self, embedding_dim: int):
        self.index.recreate_collection(
            collection_name=self.index_name,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
        )
        return
    
    def create_index(
        self, 
        items_vectors: NDArray[float],
        payload: t.Iterable[ItemPayloadDataType],
        embedding_dim: t.Optional[int]=None,
        batch_size: int=128,
    ):
        if embedding_dim is None:
            embedding_dim = items_vectors.shape[1]
        self._init_index(embedding_dim=embedding_dim)
        self.index.upload_collection(
            collection_name=self.index_name,
            vectors=items_vectors,
            payload=payload,
            ids=None,  # Vector ids will be assigned automatically
            batch_size=batch_size,  # How many vectors will be uploaded in a single request?
        )
        return self
    
    def search(
        self, 
        image: t.Optional[ImageType]=None,
        image_url: t.Optional[str]=None,
        image_embedding: t.Optional[NDArray[float]]=None,
        image_encoder: t.Optional[ImageEncoder]=None,
        top_n_results: int=5,
        show_results: bool=False,
        image_key: str='image_1',
        result_images_size: t.Optional[t.Tuple[int]]=None,
    ) -> t.List[ItemPayloadDataType]:
        
        if image_embedding is None:
            assert image_encoder is not None, (
                "In case image_embedding is not provided, image_encoder should be given!"
            )
        
        assert (
            (
                int(image is not None)
                + int(image_url is not None)
                + int(image_embedding is not None)
            ) == 1,
            "Only one of image, image_url or image_embedding should be given"
        )
        
        if image_url is not None:
            image = _get_image_file_from_url(image_url=image_url)
            query_vector = image_encoder.encode(image=image)
        elif image is not None:
            query_vector = image_encoder.encode(image=image)
        elif image_embedding is not None:
            query_vector = image_embedding
        else:
            raise ValueError('Should not get here!')
            
        
        search_result = self.index.search(
            collection_name=self.index_name,
            query_vector=query_vector,
            query_filter=None,  # If you don't want any filters for now
            limit=top_n_results,
        )
        payloads = [hit.payload for hit in search_result]
        
        if show_results:
            show_items_images(
                items_images_list=[search_result_payload[image_key] for search_result_payload in payloads],
                image_size=((300, 300) if result_images_size is None else result_images_size),
            )
        
        return payloads

    

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
    save_path: t.Optional[str]=None
) -> t.Dict[str, t.Dict[int, NDArray[float]]]:
    images_embeddings_dict = {}
    for i, (item_id, images_list) in (tqdm(enumerate(images_urls.items(), start=1), total=len(images_urls)) if verbose else enumerate(images_urls.items(), start=1)):
        try:
            for image_url in tqdm(images_list):
                image_number = int(image_url.split("/")[-1].replace('.webp', ''))
                itemid_and_img_number = f"{item_id}_{image_number}"
                img_embedding = encoder_model.encode(image_url=image_url)
                if save_path is not None:
                    # if verbose: print("\nsaving intermediate images_embeddings_dict to disc...")
                    with open(save_path, mode='ab') as outfile:
                        outfile.write(orjson.dumps({itemid_and_img_number: img_embedding.tolist()}) + b"\n")
                    # if verbose: print("\nsaving intermediate images_embeddings_dict to disc ✔")
                else:
                    images_embeddings_dict[itemid_and_img_number] = img_embedding
        except Exception as e:
            print(f"Exception raised when trying to encode image at iteration {i}!")
            print(e, end='\n')
    return images_embeddings_dict