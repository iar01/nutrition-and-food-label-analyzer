from typing import Literal

Diet = Literal["vegan", "vegetarian", "gluten_free", "lactose_free", "palm_oil_free", "nut_free"]
Allergen = Literal[
    "milk",
    "eggs",
    "peanuts",
    "nuts",
    "soy",
    "gluten",
    "fish",
    "crustaceans",
    "molluscs",
    "sesame",
    "celery",
    "mustard",
    "lupin",
    "sulphites",
]
Goal = Literal["low_sugar", "low_salt", "low_sat_fat"]
Grade = Literal["a", "b", "c", "d", "e"]
