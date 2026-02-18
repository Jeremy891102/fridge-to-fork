# Code Style Guide

This project follows the **Google Python Style Guide** with some project-specific conventions.

## Key Principles

1. **Readability**: Code should be easy to read and understand
2. **Consistency**: Follow the same patterns throughout the codebase
3. **Documentation**: All public functions and classes must have docstrings
4. **Type Hints**: Use type hints for all function signatures

## Code Formatting

### Line Length
- Maximum line length: **80 characters**
- Exceptions allowed for URLs, long strings, or imports

### Indentation
- Use **4 spaces** for indentation (no tabs)
- Continuation lines should align with opening delimiter

### Imports
- Import order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Use `isort` with Google profile to maintain import order

### Naming Conventions
- **Modules**: `lowercase_with_underscores`
- **Classes**: `CapitalizedWords` (PascalCase)
- **Functions**: `lowercase_with_underscores`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`
- **Private functions**: `_leading_underscore`
- **Private classes**: `_LeadingUnderscore`

### Docstrings
- Use Google-style docstrings
- Format:
  ```python
  """Brief description.

  Longer description if needed.

  Args:
      param1: Description of param1.
      param2: Description of param2.

  Returns:
      Description of return value.

  Raises:
      ExceptionType: Description of when this exception is raised.

  TODO:
      - List of TODO items
  """
  ```

## Code Organization

### File Structure
```python
"""Module docstring."""

# Standard library imports
import os
from pathlib import Path

# Third-party imports
import requests

# Local imports
from core.vision import image_to_ingredients

# Constants
CONSTANT_VALUE = 100

# Functions
def public_function():
    """Public function docstring."""
    pass

def _private_function():
    """Private function docstring."""
    pass
```

### TODO Comments
- Use TODO comments to mark incomplete features
- Format: `# TODO: Description of what needs to be done`
- Include TODOs in docstrings for public functions

## Type Hints

- Use type hints for all function parameters and return values
- Use `Optional[Type]` for nullable types
- Use `list[Type]` instead of `List[Type]` (Python 3.9+)
- Use `str | Path` for union types (Python 3.10+)

Example:
```python
def process_image(image_path: str | Path) -> list[str]:
    """Process an image and return results."""
    pass
```

## Error Handling

- Use specific exception types
- Include helpful error messages
- Document exceptions in docstrings
- TODO: Create custom exception classes for better error handling

## Testing

- TODO: Add unit tests for all modules
- TODO: Add integration tests for API calls
- TODO: Add end-to-end tests for the Streamlit app

## Tools

### Formatting
- **Black**: Code formatter (configured in `pyproject.toml`)
- **isort**: Import sorter (configured in `pyproject.toml`)

### Linting
- **pylint**: Code linter (configured in `pyproject.toml`)
- **mypy**: Type checker (configured in `pyproject.toml`)

### Running Tools
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
pylint app.py core/ utils/

# Type check
mypy app.py core/ utils/
```

## Project-Specific Conventions

1. **Constants**: Define module-level constants in UPPERCASE
2. **Error Messages**: Use descriptive error messages with context
3. **Function Names**: Use verb-noun pattern (e.g., `image_to_ingredients`)
4. **Module Organization**: Group related functionality in packages
5. **TODO Comments**: Mark incomplete features clearly

## Examples

### Good Example
```python
"""Process images and extract ingredients."""

from pathlib import Path
from typing import Optional

from utils.ollama_client import chat_with_image

INGREDIENT_PROMPT: str = "Extract ingredients from this image."


def image_to_ingredients(image_path: str | Path) -> list[str]:
    """Extract ingredients from an image.

    Args:
        image_path: Path to the image file.

    Returns:
        List of ingredient names.

    Raises:
        FileNotFoundError: If image file does not exist.

    TODO:
        - Add input validation
        - Improve error handling
    """
    response = chat_with_image(image_path, INGREDIENT_PROMPT)
    return [line.strip() for line in response.splitlines() if line.strip()]
```

### Bad Example
```python
import os, sys  # Multiple imports on one line
from pathlib import Path

def process(img):  # No type hints, no docstring
    x = chat_with_image(img, "prompt")  # Magic string
    return x.split("\n")  # No error handling
```
