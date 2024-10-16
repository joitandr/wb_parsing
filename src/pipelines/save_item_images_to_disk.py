import os 
from os.path import join as pjoin
from pathlib import Path
import time 
import requests
import typing as t
import json
from tqdm import tqdm

from PIL import Image
import argparse

from src.parse_utils import get_all_urls, get_catalog
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
        '--save_folder', 
        type=str,
        default=None, 
        help="Where to save items images"
    )
    parser.add_argument(
        '--sleep_every_n_iterations', 
        type=int,
        default=None, 
        help="Where to save items images"
    )
    parser.add_argument(
        '--sleep_time', 
        type=float,
        default=None, 
        help="Where to save items images"
    )
    parser.add_argument('--save_only_first_images', action='store_true', help="Increase output verbosity")
    # Parse the arguments
    args = parser.parse_args()
    return args

def save_item_images_to_disk(
    uniq_items_with_images: t.Dict[str, t.List[str]],
    save_folder: str,
    sleep_every_n_iterations: t.Optional[int]=None,
    sleep_time: t.Optional[float]=None,
    save_only_first_images: bool=False,
) -> None:

    for i, (item_id, images_list) in tqdm(enumerate(uniq_items_with_images.items())):
        if not isinstance(images_list, list):
            continue
        for j, image_url in enumerate(images_list, start=1):
            if (sleep_every_n_iterations is not None) and (i % sleep_every_n_iterations == 0):
                time.sleep(sleep_time if sleep_time is not None else 0.5)
            try:
                maybe_image_number = str(image_url.split('/')[-1].replace('.webp', ''))
                if maybe_image_number.isdigit():
                    image_number = int(maybe_image_number)
                else:
                    image_number = j
                image = Image.open(requests.get(image_url, stream=True).raw).convert("RGB") 
                image.save(pjoin(save_folder, f'item_{item_id}_image{image_number}.jpeg'))
                if save_only_first_images:
                    break
            except Exception as e:
                print(f'\nexception raised when trying to save image: {image_url}')
                print(e, end='\n')

    return 

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

    ### saving item images to disk
    save_item_images_to_disk(
        uniq_items_with_images=uniq_items_with_images,
        save_folder=args.save_folder,
        sleep_every_n_iterations=args.sleep_every_n_iterations,
        sleep_time=args.sleep_time,
        save_only_first_images=args.save_only_first_images,
    )
    