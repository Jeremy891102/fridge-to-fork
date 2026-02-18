"""Main Streamlit app for Fridge-to-Fork.

This module contains the main Streamlit application that provides the
user interface for uploading images, viewing detected ingredients, and
generating recipes.
"""

import tempfile
from pathlib import Path
from typing import Optional

import streamlit as st

from core.recipe import ingredients_to_recipe
from core.vision import image_to_ingredients

# Page configuration
PAGE_TITLE: str = "Fridge-to-Fork"
PAGE_ICON: str = "🍳"
SUPPORTED_FORMATS: list[str] = ["jpg", "jpeg", "png"]


def _save_uploaded_file(uploaded_file) -> Path:
    """Save uploaded file to temporary location.

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        Path to the temporary file.

    TODO:
        - Add file size validation
        - Add file format validation
        - Use more secure temporary file handling
        - Add cleanup on app exit
    """
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(
        suffix=suffix, delete=False
    ) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return Path(tmp_file.name)


def _display_ingredients(ingredients: list[str]) -> None:
    """Display detected ingredients in the UI.

    Args:
        ingredients: List of ingredient names.

    TODO:
        - Add ingredient editing capability
        - Add ingredient removal buttons
        - Add ingredient categorization display
        - Add ingredient images/icons
        - Support ingredient quantity display
    """
    st.subheader("Detected ingredients")
    # TODO: Improve display format (cards, grid layout)
    st.write(", ".join(ingredients))


def _display_recipe(recipe: str) -> None:
    """Display generated recipe in the UI.

    Args:
        recipe: Recipe text to display.

    TODO:
        - Add recipe formatting/parsing
        - Add recipe save functionality
        - Add recipe sharing capability
        - Add recipe rating/feedback
        - Add print-friendly format
        - Support recipe export (PDF, text file)
    """
    st.subheader("Recipe")
    st.markdown(recipe)
    # TODO: Add action buttons (save, share, print)


def main() -> None:
    """Run the Fridge-to-Fork Streamlit UI.

    Main entry point for the Streamlit application. Handles the complete
    user flow: image upload → ingredient detection → recipe generation.

    TODO:
        - Add session state management for multi-step workflows
        - Add error handling and user-friendly error messages
        - Add loading states and progress indicators
        - Add image preview before processing
        - Support multiple image uploads
        - Add recipe history/saved recipes
        - Add user preferences (dietary restrictions, cuisine type)
        - Add recipe customization options
        - Implement proper logging
        - Add analytics/tracking
        - Support dark mode
        - Add responsive design improvements
        - Add accessibility features
    """
    st.set_page_config(
        page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered"
    )
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.caption(
        "Upload a photo of your fridge or ingredients to get a recipe."
    )

    # TODO: Add sidebar for settings/preferences
    # - Dietary restrictions
    # - Cuisine preferences
    # - Model selection
    # - Advanced options

    uploaded_file = st.file_uploader(
        "Upload an image", type=SUPPORTED_FORMATS
    )
    if not uploaded_file:
        st.info("Upload an image to start.")
        return

    # TODO: Add image preview
    # st.image(uploaded_file, caption="Uploaded image")

    # Save uploaded file temporarily
    tmp_path = _save_uploaded_file(uploaded_file)

    try:
        # Detect ingredients
        with st.spinner("Detecting ingredients…"):
            # TODO: Add progress bar
            # TODO: Add error handling with try-except
            ingredients = image_to_ingredients(tmp_path)

        if not ingredients:
            st.warning("No ingredients detected. Try another image.")
            return

        # Display ingredients
        _display_ingredients(ingredients)

        # TODO: Add ingredient editing interface
        # - Allow users to add/remove ingredients
        # - Allow users to correct ingredient names

        # Generate recipe button
        if st.button("Generate recipe"):
            with st.spinner("Generating recipe…"):
                # TODO: Add progress bar
                # TODO: Add error handling with try-except
                # TODO: Get user preferences from sidebar
                recipe = ingredients_to_recipe(ingredients)

            if not recipe:
                st.error("Failed to generate recipe. Please try again.")
                return

            # Display recipe
            _display_recipe(recipe)

            # TODO: Add recipe actions
            # - Save recipe button
            # - Share recipe button
            # - Generate another recipe button
            # - Rate recipe

    finally:
        # Cleanup temporary file
        # TODO: Ensure cleanup happens even on errors
        tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
