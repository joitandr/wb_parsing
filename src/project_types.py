import typing as t
CategoryWithHierarchyType = t.Dict[str, t.Dict[t.Any, t.Any]]
CatalogType = t.List[CategoryWithHierarchyType]
FlattenCategoriesType = t.List[t.Dict[str, str]]
"""
[
    {
        'category_id': 1234,
        'name': 'Сертификаты Wildberries',
        'query': None,
        'shard': None
    },
    {
        'category_id': 306,
        'name': 'Женщинам',
        'query': 'cat=306',
        'shard': 'blackhole'
    },
    {
        'category_id': 8126,
        'name': 'Блузки и рубашки',
        'products': {
            '100125460': {
                'card_url': 'https://basket-05.wbbasket.ru/vol1001/part100125/100125460/info/ru/card.json',
                'item_images_urls': [
                        'https://basket-05.wbbasket.ru/vol1001/part100125/100125460/images/big/1.webp',
                        'https://basket-05.wbbasket.ru/vol1001/part100125/100125460/images/big/2.webp',
                        ...
                    ],
            '97219146': {
                'card_url': 'https://basket-05.wbbasket.ru/vol972/part97219/97219146/info/ru/card.json',
                'item_images_urls': [
                        'https://basket-05.wbbasket.ru/vol972/part97219/97219146/images/big/1.webp',
                        'https://basket-05.wbbasket.ru/vol972/part97219/97219146/images/big/2.webp',
                        ...
                    ],
        },
    },
    ...
]
"""
ItemsWithImagesType = t.Dict[str, t.List[str]]
"""
{
    '39565985': [
        'https://basket-03.wbbasket.ru/vol395/part39565/39565985/images/big/1.webp',
        'https://basket-03.wbbasket.ru/vol395/part39565/39565985/images/big/2.webp',
        ...
        ],
    '80012708': [
        'https://basket-05.wbbasket.ru/vol800/part80012/80012708/images/big/1.webp',
        'https://basket-05.wbbasket.ru/vol800/part80012/80012708/images/big/2.webp',
        'https://basket-05.wbbasket.ru/vol800/part80012/80012708/images/big/3.webp',
        ...
    ]
}
"""
