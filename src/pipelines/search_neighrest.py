import os 
from os.path import join as pjoin
from pathlib import Path
import time 
import requests
import typing as t
import json
from pprint import pprint
from tqdm import tqdm

import numpy as np
from PIL import Image
import argparse

from src.ml.utils import (
    VectorIndex,
    ImageEncoder,
)


def parse_args():
    # Initialize the parser
    parser = argparse.ArgumentParser(description="A simple argument parser example")
    # Add arguments
    parser.add_argument(
        '--image_url', 
        type=str,
        default=None, 
        help="Search neighrest items to item on this image url"
    )
    parser.add_argument(
        '--save_path', 
        type=str,
        default=None, 
        help="Where to save search results (.json object)"
    )
    parser.add_argument(
        '--vector_index_name', 
        type=str,
        default=None, 
    )
    parser.add_argument(
        '--image_encoder_name', 
        type=str,
        default='google/vit-base-patch16-224-in21k', 
    )
    parser.add_argument(
        '--n_neighbours', 
        type=int,
        default=5, 
        help="How many neightbours to return"
    )
    # Parse the arguments
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    
    args = parse_args()
    
    #### Loading image encoder
    image_encoder = ImageEncoder(model_str=args.image_encoder_name)
    #### Loading vector index
    vector_index = VectorIndex(
        url="http://localhost:6333", 
        index_name=(args.vector_index_name if args.vector_index_name is not None else 'wb_images_v2'),
    )
    #### Searching for neightbours
    results = vector_index.search(
        image_url=args.image_url,
        image_encoder=image_encoder,
        top_n_results=args.n_neighbours,
        show_results=False
    )
    print()
    pprint(results)
    
    if args.save_path is not None:
        json.dump(results, open(args.save_path, mode='w', encoding='utf-8'))