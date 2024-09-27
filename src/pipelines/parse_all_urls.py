import os 
from os.path import join as pjoin
import time 
import requests
import typing as t
import json
from tqdm import tqdm

from furl import furl
from PIL import Image
from io import BytesIO
import argparse

from src.parse_utils import get_all_urls, get_catalog


def parse_args():
    # Initialize the parser
    parser = argparse.ArgumentParser(description="A simple argument parser example")
    # Add arguments
    parser.add_argument(
        '--save_path', 
        type=str,
        default=None, 
        help="The city where the person lives (optional)"
    )
    # Parse the arguments
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    
    args = parse_args()
    
    catalog = get_catalog()
    all_urls = get_all_urls(
        catalog=catalog,
        save_path=args.save_path
    )