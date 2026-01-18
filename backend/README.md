# FileX Backend

Backend service for semantic file indexing and search using text embeddings.

## Project Structure

```
backend/
├── src/
│   └── filex/
│       └── embedding/
│           ├── __init__.py          # Module exports
│           ├── interfaces.py        # Protocols and ABCs
│           ├── handler.py           # Main TextEmbeddingHandler class
│           ├── embedders.py         # Embedder implementations
│           ├── chunkers.py          # Chunking strategy implementations
│           ├── file_extractors.py   # File extraction utilities
│           ├── repository.py        # Repository management
│           ├── index_manager.py    # File index tracking
│           ├── storage_manager.py   # Embedding storage
│           ├── search_manager.py    # Search index management
│           └── repo_manager.py      # Repository operations
├── filex.py                         # CLI entrypoint
├── requirements.txt
├── pyproject.toml
└── example_usage.py
```

## Installation

```bash
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .
```

## CLI Usage

FileX provides a command-line interface for indexing and searching files.

### Indexing Files

Index all files in the repository:

```bash
python filex.py index
```

Index a specific file or directory:

```bash
python filex.py index path/to/file.txt
python filex.py index path/to/directory
```

Force reindexing even if files haven't changed:

```bash
python filex.py index --force
```

Index only specific file types:

```bash
python filex.py index --extensions .txt .docx
```

Use a specific embedding model (see root README.md for available models):

```bash
python filex.py index --model all-mpnet-base-v2
python filex.py index --model all-MiniLM-L6-v2
```

### Searching Files

Search for content using natural language queries:

```bash
python filex.py search "types of fruits"
```

Specify the number of results using flags:

```bash
python filex.py search "types of fruits -count 5"
python filex.py search "types of fruits --3"
python filex.py search "types of fruits" --count 3
```

The search supports various query formats:
- `"query text"` - Default 10 results
- `"query text -count 5"` - 5 results
- `"query text --3"` - 3 results
- `"query text" --count 3` - 3 results (using separate flag)

Use a specific embedding model (must match the model used for indexing):

```bash
python filex.py search "query" --model all-mpnet-base-v2
```

**Important**: The model used for searching must match the model used for indexing.

### Repository Status

View repository statistics:

```bash
python filex.py status
```

## Programmatic Usage

### Basic Usage with Dependency Injection

```python
from src.filex.embedding import (
    TextEmbeddingHandler,
    SentenceTransformerEmbedder,
    FixedSizeChunker,
)

# Default model: all-mpnet-base-v2 (768 dimensions, high-quality semantic embeddings)
embedder = SentenceTransformerEmbedder(model_name="all-mpnet-base-v2")
chunker = FixedSizeChunker(chunk_size=512, overlap=50)

handler = TextEmbeddingHandler(embedder=embedder, chunker=chunker)

chunks, embeddings = handler.embed_file("document.txt")
```

**Embedding Models**: FileX uses high-dimensional embedding techniques (384-1024 dimensions) for semantic search. See the root README.md for detailed information about available models and their usage.

### Repository Management

```python
from src.filex.embedding import (
    RepositoryManager,
    FileProcessorRouter,
    TextFileHandler,
    TextEmbeddingHandler,
    SentenceTransformerEmbedder,
    FixedSizeChunker,
)

# Use high-dimensional embeddings (768 dimensions) for better semantic search
embedder = SentenceTransformerEmbedder(model_name="all-mpnet-base-v2")
chunker = FixedSizeChunker(chunk_size=512, overlap=50)
embedding_handler = TextEmbeddingHandler(embedder=embedder, chunker=chunker)

text_handler = TextFileHandler(embedding_handler=embedding_handler)
processor = FileProcessorRouter(text_handler=text_handler)

repo_manager = RepositoryManager(processor=processor)

result = repo_manager.index_file("document.txt")
stats = repo_manager.index_directory("path/to/directory")
status = repo_manager.get_index_status()
```

### Semantic Search

```python
from src.filex.embedding import (
    RepositoryManager,
    FileProcessorRouter,
    TextFileHandler,
    TextEmbeddingHandler,
    SentenceTransformerEmbedder,
    FixedSizeChunker,
)

# High-dimensional embeddings (768 dimensions) for semantic search
embedder = SentenceTransformerEmbedder(model_name="all-mpnet-base-v2")
chunker = FixedSizeChunker(chunk_size=512, overlap=50)
embedding_handler = TextEmbeddingHandler(embedder=embedder, chunker=chunker)

text_handler = TextFileHandler(embedding_handler=embedding_handler)
processor = FileProcessorRouter(text_handler=text_handler)

repo_manager = RepositoryManager(processor=processor)
search_manager = repo_manager.search_manager

query_embedding = embedding_handler.embed_text("types of fruits")[1]
if query_embedding.ndim > 1 and query_embedding.shape[0] == 1:
    query_embedding = query_embedding[0]

results = search_manager.search(query_embedding, top_k=5)
for result in results:
    print(f"{result.file_name}: {result.chunk_text[:100]}...")
    print(f"  Similarity: {result.similarity_score:.4f}")
```

### Changing Chunking Strategy

```python
from src.filex.embedding import SentenceAwareChunker

sentence_chunker = SentenceAwareChunker(target_chunk_size=500, max_chunk_size=1000)
handler.set_chunker(sentence_chunker)

chunks, embeddings = handler.embed_text("Long document text...")
```

### Custom Embedder

Any class implementing the `Embedder` protocol can be injected:

```python
class CustomEmbedder:
    def embed(self, text: str) -> np.ndarray:
        # Your implementation
        pass
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        # Your implementation
        pass

embedder = CustomEmbedder()
handler = TextEmbeddingHandler(embedder=embedder)
```

## Architecture

### Repository Structure

FileX uses a `.filex` directory (similar to `.git`) to store:
- `index/` - Index database and search index
- `embeddings/` - Stored embedding vectors
- `metadata/` - File metadata

The repository is automatically found by walking up the directory tree from the current working directory.

### Incremental Indexing

Files are indexed incrementally, and search data is updated immediately after each file is processed. This ensures that:
- Search remains up-to-date during indexing
- Large indexing operations don't require waiting until completion to search
- Indexing and search data are kept separate for better performance

### Dependency Injection

The `TextEmbeddingHandler` uses dependency injection for both the embedder and chunker components, following OOP principles and allowing for flexible configuration.

### Chunking Strategies

- **FixedSizeChunker**: Splits text into fixed-size chunks with optional overlap
- **SentenceAwareChunker**: Respects sentence boundaries while maintaining target chunk size

Larger documents automatically produce more chunks and thus more embedding vectors.

### Search Index

The search index is maintained separately from the file index:
- File index tracks which files are indexed and their metadata
- Search index contains embeddings and chunks for semantic search
- Search index is updated incrementally as files are indexed

### Pre/Post Conditions

All public methods include documented preconditions and postconditions to ensure correctness and help with debugging.

## Supported File Types

- `.txt` - Plain text files
- `.docx` - Microsoft Word documents

Additional file types can be added by extending `FileExtractor`.
