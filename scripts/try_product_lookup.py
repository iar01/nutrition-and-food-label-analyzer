import sys

from labellens.tools.products import ProductRepo

code = sys.argv[1]
product = ProductRepo().get(code)
if product is None:
    print("not found")
else:
    for key in [
        "code",
        "name",
        "brand",
        "ingredients",
        "allergens_tags",
        "traces_tags",
        "additives_tags",
        "nutriscore_grade",
        "nova_group",
        "diet_vegan",
        "diet_gluten_free",
        "sugars_g",
        "salt_g",
        "categories_tags",
    ]:
        print(f"{key}: {product.get(key)}")
