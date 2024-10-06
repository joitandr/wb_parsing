import os 
from os.path import join as pjoin
from pathlib import Path
import time 
import requests
import typing as t
import json
from tqdm import tqdm

import orjson
import numpy as np
from furl import furl
from PIL import Image
from io import BytesIO
import argparse

from src.parse_utils import get_all_urls, get_catalog
from src.ml.utils import (
    ImageEncoder,
    encode_images
)
from src.utils import (
    get_uniq_items_with_images,
)


ROOT_PATH = str(Path(os.getenv('PYTHONPATH')))

def parse_args():
    # Initialize the parser
    parser = argparse.ArgumentParser(description="A simple argument parser example")
    # Add arguments
    parser.add_argument(
        '--all_urls_path', 
        type=str,
        default=None, 
        help="Where to save items embeddings"
    )
    parser.add_argument(
        '--save_path', 
        type=str,
        default=None, 
        help="Where to save items embeddings"
    )
    # Parse the arguments
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    
    args = parse_args()
    
    ### getting all parsed urls
    all_urls = json.load(open(
        args.all_urls_path if args.all_urls_path is not None
        else pjoin(ROOT_PATH, 'raw_data/all_urls_from_tmux.json')
    ))
    print(f"#all_urls: {len(all_urls):,}")
    
    ### getting unique items
    uniq_items_with_images = get_uniq_items_with_images(
        flatten_categories=all_urls,
        verbose=True
    )
    print(f"#uniq_items_with_images: {len(uniq_items_with_images):,}")

    ### Encode images
    print("\nEncoding item images...")
    image_encoder = ImageEncoder(model_str='google/vit-base-patch16-224-in21k')
    images_embeddings = encode_images(
        images_urls={item_id: images_urls_list for i, (item_id, images_urls_list) in enumerate(uniq_items_with_images.items())},
        encoder_model=image_encoder,
        save_path=args.save_path,
        verbose=True
    )
    print("Encoding item images ✔")
    # Convert numpy arrays to lists before serializing
    # images_embeddings_serializable = {key: value.tolist() for key, value in tqdm(images_embeddings.items(), desc='convering np.arrays to lists')}
    # print("\nSaving images embeddings to disc...")
    # with open(args.save_path, mode='wb') as f:
    #     f.write(orjson.dumps(images_embeddings_serializable))
    # print("Saving images embeddings to disc ✔")
    # images_embs_array = np.array([
    #     emb 
    #     for item_id, item_image_emb_dict in images_embeddings.items() 
    #         for image_number, emb in item_image_emb_dict.items()
    # ])
    print(f"#images_embeddings: {len(images_embeddings):,}")