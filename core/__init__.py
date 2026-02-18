"""Core logic: vision (image → ingredients) and recipe (ingredients → recipe).

This package contains the core business logic for converting images to
ingredient lists and generating recipes from ingredients.
"""

from core.recipe import ingredients_to_recipe
from core.vision import image_to_ingredients

__all__ = ["image_to_ingredients", "ingredients_to_recipe"]
