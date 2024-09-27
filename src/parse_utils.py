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

CategoryWithHierarchyType = t.Dict[str, t.Dict[t.Any, t.Any]]
CatalogType = t.List[CategoryWithHierarchyType]
FlattenCategoriesType = t.List[t.Dict[str, str]]

CATALOG_URL = 'https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v2.json'

def get_catalog(catalog_url: str=CATALOG_URL) -> CatalogType:
    catalog = requests.get(catalog_url).json()
    return catalog


def find_card_url(
    item_id: t.Union[int, str],
    max_retries: int=40,
    sleep_time: float=0.1,
    verbose: bool=False,
    start_basket_number: t.Optional[int]=None,
    max_basket_number: int=30,
) -> (str, bool):
    
    success_flag = False 
    part = str(item_id)[:-3]
    vol = part[:-2]
    retry_count = 0
    basket_number = (
        start_basket_number if start_basket_number is not None else 1
    )
    while not success_flag:
        if retry_count == max_retries:
            break 
        basket_number = basket_number % max_basket_number
        try:
            basket = f"0{basket_number}" if basket_number <= 9 else str(basket_number)
            item_url = (
                f"https://basket-{basket}.wbbasket.ru/"
                f"vol{vol}/part{part}/{item_id}/info/ru/card.json"
            )
            item_info = json.loads(requests.get(item_url).content)
            success_flag = True
        except:
            if verbose: print(f"{retry_count}: Not {item_url}", end='\n')
            retry_count += 1
            basket_number += 1
            time.sleep(sleep_time)
            
    return item_url, success_flag

def get_images_urls_from_card_url(
    card_url: str,
    n_images: t.Optional[int]=None,
    verify: bool=False
) -> t.List[str]:
    url = furl(card_url)
    base_image_url = pjoin(url.origin, "/".join(url.path.segments[:-3]), 'images/big/1.webp')
    images_urls_list = []
    if n_images is None:
        # trying to figure out amount of images from card_url
        try:
            n_images = int(json.loads(requests.get(card_url).content)['media']['photo_count'])
        except:
            pass
            
    if verify:
        n_images_parsed = 0
        image_number = 1
        first_fail_flag = False
        while (not first_fail_flag):
            try:
                current_image_url = base_image_url.replace('1.webp', f"{image_number}.webp")
                content = requests.get(current_image_url).content
                item_img = Image.open(BytesIO(content))
                n_images_parsed += 1
                images_urls_list.append(current_image_url)
            except:
                first_fail_flag = True
                
            image_number += 1
            if n_images is not None and n_images_parsed >= n_images:
                break 
    else:
        n_plus_one_failed, n_succeeded = False, False
        if n_images is not None:
            try:
                current_image_url = base_image_url.replace('1.webp', f"{n_images+1}.webp")
                content = requests.get(current_image_url).content
                item_img = Image.open(BytesIO(content))
                n_plus_one_failed = False
            except:
                n_plus_one_failed = True 
                
            try:
                current_image_url = base_image_url.replace('1.webp', f"{n_images}.webp")
                content = requests.get(current_image_url).content
                item_img = Image.open(BytesIO(content))
                n_succeeded = True
            except:
                n_plus_one_failed = False
                
            if n_succeeded and n_plus_one_failed:
                for image_number in range(1, n_images+1):
                    images_urls_list.append(base_image_url.replace('1.webp', f"{image_number}.webp"))
            else:
                images_urls_list.append(base_image_url)
        else:
            images_urls_list.append(base_image_url)
            
    return images_urls_list

def construct_browse_url(
    query: str,
    shard: str,
) -> str:
    browse_cat_url = furl(f'https://catalog.wb.ru/catalog/{shard}/v2/catalog?ab_testing=false')
    browse_cat_url.add({'appType': '1'})
    browse_cat_url.add({'curr': 'rub'})
    browse_cat_url.add({'dest': '-446116'})
    browse_cat_url.add({'sort': 'popular'})
    browse_cat_url.add({'spp': '30'})
    browse_cat_url.add({'uclusters': '0'})
    browse_cat_url.add(query)
    return browse_cat_url.url

def dfs(category, categories_list: t.List[t.Dict[str, str]]):
    # Print the current category's information
    # print(f"Name: {category.get('name')}, Shard: {category.get('shard')}, Query: {category.get('query')}")
    categories_list.append({
        "category_id": category.get("id"),
        "name": category.get('name'),
        'shard': category.get('shard'),
        'query': category.get('query')
    })
    
    # If there are child categories, recursively call dfs on each one
    if 'childs' in category:
        for child in category['childs']:
            dfs(child, categories_list)
        
def get_browse_categories_with_urls(
    catalog: CatalogType
) -> FlattenCategoriesType:
    
    categories_list = []    
    for one_category in catalog:
        dfs(category=one_category, categories_list=categories_list)

    for category in tqdm(categories_list):
        if category['shard'] == 'blackhole' or category['shard'] is None:
            continue
        browse_result_url = construct_browse_url(
            query=category["query"],
            shard=category['shard']
        )
        category['url'] = browse_result_url
    return categories_list
    
def get_all_urls(
    catalog: CatalogType,
    save_path: t.Optional[str]=None,
) -> FlattenCategoriesType:
    
    flatten_categories_with_urls = get_browse_categories_with_urls(catalog=catalog)
    for flatten_category in tqdm(flatten_categories_with_urls, desc='flatten_categories_with_urls'):
        url = flatten_category.get('url')
        if url is None:
            continue 
        try:
            category_products = json.loads(requests.get(url).content)
        except Exception as e:
            category_products = []
            continue
        
        items_metadata = {}
        for i, item_metadata in tqdm(enumerate(category_products['data']['products'], start=1)):
            if i % 20 == 0:
                time.sleep(4)
            item_id = item_metadata['id']
            card_url, success_flag = find_card_url(
                item_id=item_id,
                max_retries=40,
                sleep_time=0.1,
                verbose=False,
                start_basket_number=10,
                max_basket_number=30
            )
            if success_flag:
                items_metadata[item_id] = {'card_url': card_url}
                item_images_urls = get_images_urls_from_card_url(
                    card_url=card_url,
                    n_images=None,
                    verify=True
                )
                items_metadata[item_id]['item_images_urls'] = item_images_urls
        flatten_category['products'] = items_metadata
        if save_path is not None:
            json.dump(flatten_categories_with_urls, open(save_path, mode='w', encoding='utf-8'))
    return flatten_categories_with_urls


    
    