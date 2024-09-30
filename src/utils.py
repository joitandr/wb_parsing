from tqdm import tqdm

from src.project_types import (
    FlattenCategoriesType,
    ItemsWithImagesType,
)

def get_uniq_items_with_images(
    flatten_categories: FlattenCategoriesType,
    verbose: bool=False
) -> ItemsWithImagesType:
    """
    Leaves only unique items (with their images) from all items in flatten_categories
    Args:
        flatten_categories (FlattenCategoriesType): _description_
        verbose (bool, optional): _description_. Defaults to False.
    Returns:
        ItemsWithImagesType: _description_
    """

    uniq_items_with_images = {}
    for category in (tqdm(flatten_categories, desc='flatten_categories') if verbose else flatten_categories):
        products_metadata = category.get('products')
        if products_metadata is None:
            continue
        for item_id, item_metadata in products_metadata.items():
            if item_id not in uniq_items_with_images:
                uniq_items_with_images[item_id] = item_metadata['item_images_urls']
    return uniq_items_with_images