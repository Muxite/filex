# Coding Guidelines

This document outlines the coding standards and best practices for the FileX backend project. Follow these guidelines to maintain consistency and code quality.

## Table of Contents

- [Project Structure](#project-structure)
- [Object-Oriented Programming](#object-oriented-programming)
- [Dependency Injection](#dependency-injection)
- [Documentation](#documentation)
- [Type Hints](#type-hints)
- [Error Handling](#error-handling)
- [Code Style](#code-style)

## Project Structure

The project follows a modular structure with clear separation of concerns:

```
backend/
├── src/
│   └── filex/
│       └── embedding/
│           ├── __init__.py          # Module exports
│           ├── interfaces.py        # Protocols and ABCs
│           ├── handler.py           # Main business logic
│           ├── embedders.py         # Implementations
│           ├── chunkers.py          # Strategy implementations
│           └── file_extractors.py   # Utility classes
├── requirements.txt
├── pyproject.toml
└── README.md
```

**Guidelines:**
- Use `src/` layout for packages
- Separate interfaces/protocols from implementations
- Group related functionality into modules
- Keep module files focused and cohesive

## Object-Oriented Programming

### Principles

1. **Single Responsibility Principle**: Each class should have one reason to change
2. **Open/Closed Principle**: Open for extension, closed for modification
3. **Dependency Inversion**: Depend on abstractions, not concretions
4. **Interface Segregation**: Keep interfaces focused and minimal

### Class Design

```python
"""
Good: Clear purpose, well-documented
"""
class FixedSizeChunker(Chunker):
    """
    Chunks text into fixed-size pieces with optional overlap.
    
    Larger documents produce more chunks automatically.
    """
    
    def __init__(self, chunk_size: int, overlap: int = 0):
        """
        Initialize chunker with fixed chunk size.
        
        :param chunk_size: Number of characters per chunk (must be > 0)
        :param overlap: Number of overlapping characters between chunks
        """
        # Validation and initialization
        pass
```

**Guidelines:**
- Use abstract base classes (ABC) or Protocols for interfaces
- Document class purpose in the docstring
- Validate inputs in constructors
- Keep classes focused on a single concern

## Dependency Injection

Always use dependency injection for external dependencies and components.

### Constructor Injection (Preferred)

```python
class TextEmbeddingHandler:
    def __init__(self, embedder: Embedder, chunker: Optional[Chunker] = None):
        """
        :param embedder: The embedder to use (injected dependency, must not be None)
        :param chunker: The chunking strategy to use (optional)
        """
        if embedder is None:
            raise ValueError("embedder cannot be None")
        self.embedder = embedder
        # ...
```

**Benefits:**
- Testability: Easy to inject mocks/test doubles
- Flexibility: Can swap implementations without changing code
- Clarity: Dependencies are explicit

**Guidelines:**
- Inject dependencies through constructors
- Validate injected dependencies are not None
- Use type hints to make dependencies clear
- Prefer Protocols over concrete types for injection points

## Documentation

### Docstring Format

Use Google-style docstrings with Javadoc-style parameter documentation.

```python
def embed_text(self, text: str) -> Tuple[List[str], np.ndarray]:
    """
    Chunk text and generate embeddings for each chunk.
    
    :param text: The text to embed (must not be empty)
    :returns: Tuple of (chunks, embeddings) where embeddings is a 2D array
    :postcondition: embeddings.shape[0] == len(chunks)
    :raises ValueError: If text is empty
    """
```

### When to Use Pre/Post Conditions

**Use pre/post conditions for:**
- Non-trivial guarantees (e.g., "embeddings.shape[0] == len(chunks)")
- Important invariants (e.g., "result >= 1")
- Complex constraints (e.g., parameter relationships)

**Do NOT use pre/post conditions for:**
- Obvious type guarantees (e.g., "result is not None" when return type is `str`)
- Simple assignments (e.g., "self.value == value" after assignment)
- Type system guarantees (e.g., "text is not None" when parameter is `str: str`)

**Best Practice:**
- Include constraints directly in parameter descriptions: `(must be > 0)`, `(must not be None)`
- Include guarantees in return descriptions: `(always >= 1)`, `(all non-empty strings)`
- Only use `:precondition:` and `:postcondition:` tags for complex or critical guarantees

### Example Documentation Levels

```python
"""
Minimal - for simple methods
"""
def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.
    
    :param file_path: Path to the file (must exist)
    :returns: File size in bytes (always >= 0)
    """

"""
Medium - for important methods
"""
def embed_text(self, text: str) -> Tuple[List[str], np.ndarray]:
    """
    Chunk text and generate embeddings for each chunk.
    
    :param text: The text to embed (must not be empty)
    :returns: Tuple of (chunks, embeddings) where embeddings is a 2D array
    :postcondition: embeddings.shape[0] == len(chunks)
    :raises ValueError: If text is empty
    """

"""
Detailed - for complex methods or public APIs
"""
def __init__(self, chunk_size: int, overlap: int = 0):
    """
    Initialize chunker with fixed chunk size.
    
    :param chunk_size: Number of characters per chunk (must be > 0)
    :param overlap: Number of overlapping characters between chunks
        (must be >= 0 and < chunk_size)
    :raises ValueError: If chunk_size <= 0 or overlap is invalid
    """
```

## Type Hints

Always use type hints for function parameters, return types, and class attributes.

```python
from typing import List, Optional, Tuple
import numpy as np

def chunk(self, text: str) -> List[str]:
    """..."""

def embed_batch(self, texts: List[str]) -> np.ndarray:
    """..."""
```

**Guidelines:**
- Use `typing` module for complex types (List, Dict, Tuple, Optional, etc.)
- Use `np.ndarray` for NumPy arrays
- Avoid `Any` unless absolutely necessary
- Use `Protocol` for structural subtyping

## Error Handling

### Validation

Validate inputs and raise appropriate exceptions:

```python
def __init__(self, chunk_size: int, overlap: int = 0):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")
```

### Exception Types

- Use `ValueError` for invalid parameter values
- Use `FileNotFoundError` for missing files
- Use `TypeError` for type mismatches
- Use custom exceptions for domain-specific errors

### Error Messages

- Be specific and actionable
- Include the parameter name when relevant
- Explain what went wrong and why

```python
# Good
raise ValueError("chunk_size must be positive")

# Bad
raise ValueError("invalid input")
```

## Code Style

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `TextEmbeddingHandler`)
- **Functions/Methods**: `snake_case` (e.g., `embed_text`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_CHUNK_SIZE`)
- **Private methods**: Prefix with `_` (e.g., `_split_into_sentences`)
- **Type variables**: Use descriptive names (e.g., `T_co` for covariant)

### Formatting

- Follow PEP 8
- Use 4 spaces for indentation
- Maximum line length: 100 characters (soft limit)
- Use blank lines to separate logical sections
- Remove trailing whitespace

### Imports

```python
# Standard library imports
from typing import List, Optional
from pathlib import Path

# Third-party imports
import numpy as np
from sentence_transformers import SentenceTransformer

# Local imports
from .interfaces import Embedder, Chunker
from .file_extractors import FileExtractor
```

**Guidelines:**
- Group imports: stdlib, third-party, local
- Use absolute imports for clarity
- Avoid wildcard imports (`from module import *`)
- Prefer specific imports over generic ones

### Comments

```python
"""
Good: Explain why, not what
"""
chunks = []
step = self.chunk_size - self.overlap  # Calculate step size accounting for overlap
start = 0

"""
Bad: States the obvious
"""
chunks = []  # Initialize empty list
start = 0  # Set start to 0
```

## Testing

### Test Organization

- Mirror source structure in tests
- One test file per module: `test_handler.py`, `test_chunkers.py`
- Use descriptive test names: `test_chunk_handles_empty_text()`

### Test Structure

```python
def test_fixed_chunker_produces_correct_count():
    """Test that FixedSizeChunker produces expected number of chunks."""
    chunker = FixedSizeChunker(chunk_size=100, overlap=10)
    text = "a" * 500
    
    chunks = chunker.chunk(text)
    
    assert len(chunks) > 0
    assert all(len(chunk) <= 100 for chunk in chunks)
```

## Best Practices Summary

1. **Dependency Injection**: Always inject dependencies, never hardcode them
2. **Type Hints**: Use type hints everywhere
3. **Validation**: Validate inputs at boundaries (constructors, public methods)
4. **Documentation**: Document public APIs thoroughly, internal code minimally
5. **Pre/Post Conditions**: Only for non-trivial, important guarantees
6. **Error Messages**: Be specific and helpful
7. **Single Responsibility**: Keep classes and methods focused
8. **Testing**: Write tests for all public methods

## Additional Resources

- [PEP 8 - Style Guide](https://pep8.org/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Design Patterns in Python](https://refactoring.guru/design-patterns/python)
