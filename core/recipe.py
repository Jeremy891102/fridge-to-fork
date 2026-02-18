"""Ingredient list → recipe logic.

This module handles the conversion of ingredient lists to recipe
suggestions using the Ollama text generation API.
"""

from typing import Optional
from utils.ollama_client import generate_text as chat_text_only

import re

# Recipe prompt template


RECIPE_PROMPT_TEMPLATE = """
You are an experienced home chef who thinks practically and creatively.

You have access to the following current ingredients:
{inv}

You can:
- Create recipes (simple or detailed)
- Suggest substitutions
- Recommend storage methods or shelf life
- Suggest meal ideas based on what's available
- Answer general food-related questions

Guidelines:
- Prioritize using available ingredients.
- You may assume common pantry staples (salt, pepper, oil, sugar, flour, etc.) when reasonable.
- If something essential is missing, clearly explain what's needed and suggest alternatives.
- Respond naturally, like a real chef speaking to a home cook.
- Adapt detail level to the user's question — short answers for simple questions, full recipes when asked.
- If the question is not food-related, politely redirect to cooking topics.

If giving a recipe, structure it clearly (name, ingredients, steps), but you do NOT need to follow a rigid template.

Conversation so far:
{history_txt}

USER: {user_message}
ASSISTANT:
"""


def chat_with_chef(
    user_message: str,
    inventory: list[str],
    history: list[dict],
) -> str:
    inv = _format_list(inventory)
    history_txt = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in history[-6:]
    )
    prompt = RECIPE_PROMPT_TEMPLATE.format(
        inv=inv, history_txt=history_txt, user_message=user_message
    )
    return chat_text_only(prompt)


def _normalize_ingredient(s: str) -> str:
    """Light normalization to stabilize prompts."""
    s = s.strip().lower()
    s = re.sub(r"^[-*•\d\.\)\s]+", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _format_list(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items)

# simple check for basic recipe structure; we can add more complex validation later
def _looks_valid(text: str) -> bool:
    if not text:
        return False

    t = text.lower()

    required_sections = [
        "recipe name:",
        "ingredients used:",
        "steps:"
    ]

    return all(section in t for section in required_sections)



def ingredients_to_recipe(
    ingredients: list[str],
    dietary_restrictions: Optional[list[str]] = None,
    cuisine_type: Optional[str] = None,
) -> str:
    """Generate a recipe from a list of ingredients.

    This function takes a list of ingredients and generates a complete
    recipe including name, ingredients list, and step-by-step instructions.

    Args:
        ingredients: List of ingredient names.
        dietary_restrictions: Optional list of dietary restrictions
            (e.g., ["vegetarian", "gluten-free"]).
        cuisine_type: Optional cuisine type preference (e.g., "Italian",
            "Asian").

    Returns:
        Full recipe text including title, ingredients, and instructions.
        Empty string if generation fails.

    Raises:
        ValueError: If ingredients list is empty.
        requests.RequestException: If the API request fails.

    TODO:
        - Add recipe formatting (markdown, structured JSON)
        - Support multiple recipe suggestions
        - Add recipe metadata (cooking time, difficulty, servings)
        - Implement dietary restrictions filtering
        - Add cuisine type preferences
        - Support recipe customization (spice level, cooking method)
        - Add ingredient substitution suggestions
        - Cache recipes for same ingredient combinations
        - Add recipe validation (ensure all ingredients are used)
        - Support recipe scaling (servings adjustment)
        - Add nutritional information generation
        - Implement recipe rating/scoring
        - Add cooking tips and variations
        - Support multi-step recipe generation with user feedback
    """
    # Input validation
    if not ingredients:
        raise ValueError("Ingredients list cannot be empty")

    normed: list[str] = []
    seen = set()
    for ing in ingredients:
        n = _normalize_ingredient(ing)
        if not n:
            continue
        if n not in seen:
            seen.add(n)
            normed.append(n)
    
    if not normed:
        raise ValueError("No valid ingredients after normalization; check input formatting")
    # Normalize ingredients before generating recipe
    ingredient_list = _format_list(normed)

    # 2) Normalize optional controls

    restrictions = dietary_restrictions or []
    restrictions = [_normalize_ingredient(r) for r in restrictions if _normalize_ingredient(r)]
    restrictions_str = ", ".join(restrictions) if restrictions else "None"

    cuisine = (cuisine_type or "").strip()
    cuisine_str = cuisine if cuisine else "Any"



    prompt = RECIPE_PROMPT_TEMPLATE.format(ingredients=ingredient_list,
                                           dietary_restrictions=restrictions_str,
                                           cuisine_type=cuisine_str)
    

    # 3) Call the model to generate a recipe
    try:
        recipe = chat_text_only(prompt)
    except Exception as e:
        print(f"Error generating recipe: {e}")
        return ""

    # Parse and validate recipe structure
    recipe = (recipe or "").strip()
    if not recipe:
        return ""



    return recipe   



def parse_recipe(recipe_text: str) -> dict[str, str]:
    """Parse a recipe text into structured components.

    Args:
        recipe_text: Raw recipe text from the model.

    Returns:
        Dictionary with keys: "name", "ingredients", "instructions".

    TODO:
        - Implement recipe parsing logic
        - Handle various recipe formats
        - Extract recipe name
        - Extract ingredients list
        - Extract step-by-step instructions
        - Extract metadata (cooking time, servings, difficulty)
        - Return structured format (dict or dataclass)
        - Handle parsing errors gracefully
    """
    # TODO: Implement parsing
    return {
        "name": "",
        "ingredients": "",
        "instructions": "",
    }


def format_recipe_markdown(recipe_data: dict[str, str]) -> str:
    """Format recipe data as markdown.

    Args:
        recipe_data: Dictionary containing recipe components.

    Returns:
        Formatted markdown string.

    TODO:
        - Implement markdown formatting
        - Add proper headings and sections
        - Format ingredients as bullet list
        - Format instructions as numbered list
        - Add metadata section (time, servings, etc.)
    """
    # TODO: Implement markdown formatting
    return ""


def validate_recipe(recipe_text: str, ingredients: list[str]) -> tuple[bool, str]:
    """Validate that a recipe uses the provided ingredients.

    Args:
        recipe_text: Recipe text to validate.
        ingredients: Original ingredient list.

    Returns:
        Tuple of (is_valid, validation_message).

    TODO:
        - Check that recipe mentions most ingredients
        - Validate recipe structure (has name, ingredients, steps)
        - Check for reasonable cooking instructions
        - Return detailed validation feedback
    """
    # TODO: Implement validation
    return True, ""
