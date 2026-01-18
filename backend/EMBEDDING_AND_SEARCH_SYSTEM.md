# FileX Embedding and Search System Architecture

This document explains how FileX's embedding and search system works, including how data structures are stored and cached in the `.filex` directory.

## Overview

FileX uses a dual-embedding system to index both text and image files:
- **Text Embeddings**: Sentence-BERT models (e.g., `all-mpnet-base-v2`, 768 dimensions) for semantic text understanding
- **Image Embeddings**: CLIP models (e.g., `openai/clip-vit-base-patch32`, 512 dimensions) for computer vision

Both systems generate high-dimensional vector embeddings that enable semantic search through cosine similarity.

## System Architecture

### Core Components

1. **RepositoryManager**: Orchestrates indexing, storage, and search operations
2. **IndexManager**: Tracks indexed files using SQLite database
3. **StorageManager**: Manages persistent storage of embeddings and metadata
4. **SearchManager**: Maintains searchable index for fast semantic queries
5. **FileProcessorRouter**: Routes files to appropriate handlers (text, image, or default)

### Data Flow

```
File → FileProcessorRouter → FileHandler → Embedder → Embeddings
                                                          ↓
                                    StorageManager → .filex/embeddings/
                                                          ↓
                                    SearchManager → .filex/index/search_index.npy
                                                          ↓
                                    IndexManager → .filex/index/index.db
```

## Embedding System

### Text Embedding Pipeline

1. **File Extraction**: `FileExtractor` reads text from files (`.txt`, `.docx`)
2. **Chunking**: `Chunker` splits large documents into smaller chunks (default: 512 characters with 50 character overlap)
3. **Embedding Generation**: `SentenceTransformerEmbedder` converts each chunk into a high-dimensional vector (768 dimensions for `all-mpnet-base-v2`)
4. **Storage**: Embeddings saved as NumPy arrays (`.npy` files)

**Example Flow**:
```
document.txt (10,000 chars)
  → Chunker → [chunk1, chunk2, ..., chunk20]
  → Embedder → [embedding1 (768D), embedding2 (768D), ..., embedding20 (768D)]
  → Storage: document_hash.npy (shape: [20, 768])
```

### Image Embedding Pipeline

1. **Image Loading**: `CLIPImageEmbedder` loads image files (`.png`, `.jpg`, `.jpeg`)
2. **Embedding Generation**: CLIP model processes entire image into a single embedding vector (512 dimensions)
3. **Storage**: Embedding saved as NumPy array (`.npy` file)

**Example Flow**:
```
photo.png
  → CLIPImageEmbedder → embedding (512D)
  → Storage: photo_hash.npy (shape: [1, 512])
```

### Embedding Models

**Text Models** (Sentence-BERT):
- `all-mpnet-base-v2` (default): 768 dimensions, high-quality semantic understanding
- `all-MiniLM-L6-v2`: 384 dimensions, faster inference
- `paraphrase-multilingual-mpnet-base-v2`: 768 dimensions, supports 50+ languages

**Image Models** (CLIP):
- `openai/clip-vit-base-patch32` (default): 512 dimensions, general-purpose vision

Models are automatically cached by `huggingface_hub` in `~/.cache/huggingface/hub/` after first download.

## Search System

### Search Index Structure

The search index is maintained separately from the file index to enable fast semantic queries:

- **Search Embeddings**: `search_index.npy` - NumPy array containing all chunk embeddings
  - Shape: `[total_chunks, embedding_dimension]`
  - Example: `[150, 768]` for 150 text chunks with 768-dimensional embeddings

- **Search Metadata**: `search_metadata.json` - JSON array mapping embeddings to chunks
  ```json
  [
    {
      "file_path": "/path/to/document.txt",
      "file_name": "document.txt",
      "chunk_index": 0,
      "chunk_text": "First chunk of text..."
    },
    ...
  ]
  ```

### Incremental Indexing

FileX updates the search index **immediately after each file is processed**, not at the end of a batch:

1. File is processed → embeddings generated
2. Embeddings saved to `.filex/embeddings/` (persistent storage)
3. Embeddings added to search index (in-memory)
4. Search index saved to disk (`.filex/index/search_index.npy`)
5. File index updated in SQLite database

This ensures:
- Search remains up-to-date during indexing
- Large indexing operations don't block search
- Indexing and search data are kept separate for performance

### Search Algorithm

1. **Query Embedding**: User's natural language query is embedded using the same model used for indexing
2. **Cosine Similarity**: Compute cosine similarity between query embedding and all chunk embeddings
3. **Ranking**: Sort results by similarity score (highest first)
4. **Top-K Results**: Return top K most similar chunks with metadata

**Mathematical Process**:
```
query_embedding (1D, 768D) → normalize
search_index (N chunks, 768D) → normalize each row
similarities = dot_product(normalized_search_index, normalized_query)
results = top_k(similarities)
```

## Data Structures in `.filex`

The `.filex` directory structure mirrors Git's approach, storing all indexing data in a hidden directory:

```
.filex/
├── index/
│   ├── index.db              # SQLite database: file tracking
│   ├── search_index.npy      # NumPy array: all chunk embeddings
│   └── search_metadata.json  # JSON: chunk metadata mapping
├── embeddings/               # Persistent embedding storage
│   ├── {file_hash}.npy       # Embeddings for each file (hash-based naming)
│   └── ...
└── metadata/                 # File metadata cache
    ├── {file_hash}.json      # Metadata for each file (hash-based naming)
    └── ...
```

### File Index Database (`index/index.db`)

SQLite database tracking all indexed files:

**Schema**:
```sql
CREATE TABLE file_index (
    file_path TEXT PRIMARY KEY,        -- Absolute path to file
    file_hash TEXT NOT NULL,           -- SHA256 hash of file contents
    file_size INTEGER NOT NULL,        -- File size in bytes
    modified_time TEXT NOT NULL,       -- ISO format timestamp
    indexed_time TEXT NOT NULL,        -- When file was indexed
    extension TEXT NOT NULL,           -- File extension (.txt, .png, etc.)
    is_text_type INTEGER NOT NULL,     -- Boolean: 1 for text, 0 for non-text
    num_chunks INTEGER,                -- Number of chunks (text files only)
    embedding_dimension INTEGER        -- Embedding dimension (text/image files)
)
```

**Purpose**:
- Track which files are indexed
- Detect file changes (hash, size, modification time comparison)
- Store file metadata for status reporting
- Enable incremental reindexing (only changed files)

### Embeddings Storage (`embeddings/{hash}.npy`)

Persistent storage of embeddings for each file:

- **Naming**: SHA256 hash of file path (e.g., `0b4c4870...npy`)
- **Format**: NumPy array (`.npy` format)
- **Structure**:
  - Text files: `[num_chunks, embedding_dim]` (e.g., `[20, 768]`)
  - Image files: `[1, embedding_dim]` (e.g., `[1, 512]`)

**Purpose**:
- Cache embeddings to avoid recomputation
- Enable fast reindexing (only regenerate if file changed)
- Support model switching (different embeddings for same file)

### Metadata Storage (`metadata/{hash}.json`)

JSON files containing file metadata and embedding information:

**Structure**:
```json
{
  "file_path": "/absolute/path/to/file.txt",
  "file_name": "file.txt",
  "file_extension": ".txt",
  "file_size_bytes": 1024,
  "file_size_kb": 1.0,
  "file_size_mb": 0.001,
  "modified_time": "2026-01-18T03:56:27.970491",
  "created_time": "2026-01-18T03:55:11.490660",
  "embeddings_info": {
    "num_chunks": 20,
    "embedding_dimension": 768
  },
  "processed": true
}
```

**Purpose**:
- Cache file metadata (size, timestamps, etc.)
- Store embedding statistics (chunk count, dimensions)
- Enable fast status reporting without re-reading files

### Search Index (`index/search_index.npy` + `search_metadata.json`)

In-memory searchable index (loaded on startup, saved after updates):

**Search Index** (`search_index.npy`):
- NumPy array: `[total_chunks, embedding_dimension]`
- Contains all chunk embeddings from all indexed files
- Updated incrementally as files are indexed

**Search Metadata** (`search_metadata.json`):
- JSON array mapping each embedding row to its source chunk
- Contains file path, chunk index, and chunk text
- Enables result formatting (showing which file/chunk matched)

**Purpose**:
- Fast semantic search (single NumPy array operation)
- Separate from file index for performance
- Updated incrementally for real-time searchability

## Indexing Process

### Single File Indexing

1. **File Detection**: `RepositoryManager.index_file()` receives file path
2. **Change Detection**: `IndexManager.has_changed()` checks:
   - File exists in index?
   - File size changed?
   - Modification time changed?
   - File hash changed?
3. **File Processing**: `FileProcessorRouter.process_file()`:
   - Routes to appropriate handler (text/image/default)
   - Handler extracts content and generates embeddings
4. **Storage**: `StorageManager.save_processing_result()`:
   - Saves embeddings to `.filex/embeddings/{hash}.npy`
   - Saves metadata to `.filex/metadata/{hash}.json`
5. **Search Index Update**: `SearchManager.add_file_embeddings()`:
   - Removes old embeddings for file (if exists)
   - Adds new embeddings to in-memory index
   - Saves search index to disk
6. **File Index Update**: `IndexManager.add_entry()`:
   - Updates SQLite database with file information

### Directory Indexing

1. **File Discovery**: Recursively scan directory (excluding `.filex`)
2. **Batch Processing**: Process each file individually (incremental updates)
3. **Progress Tracking**: `tqdm` progress bar shows indexing status
4. **Error Handling**: Continue indexing even if individual files fail

## Search Process

### Query Execution

1. **Query Parsing**: Extract query text and result count from user input
2. **Query Embedding**: `TextEmbeddingHandler.embed_text()` generates embedding for query
3. **Similarity Search**: `SearchManager.search()`:
   - Loads search index from disk (if not in memory)
   - Computes cosine similarity between query and all chunks
   - Ranks results by similarity score
4. **Result Formatting**: Returns `SearchResult` objects with:
   - File path and name
   - Chunk index and text
   - Similarity score

### Search Index Loading

On `SearchManager` initialization:
- Loads `search_index.npy` into memory (`self._embeddings`)
- Loads `search_metadata.json` into memory (`self._metadata`)
- If files don't exist, starts with empty index

On each update:
- Saves in-memory index to disk immediately
- Ensures search index is always up-to-date

## Caching Strategy

### Model Caching

- **Location**: `~/.cache/huggingface/hub/`
- **Managed by**: `huggingface_hub` library
- **Behavior**: First load downloads model, subsequent loads use cache
- **Benefit**: Avoids re-downloading large models (hundreds of MB)

### Embedding Caching

- **Location**: `.filex/embeddings/{hash}.npy`
- **Key**: SHA256 hash of file path
- **Invalidation**: File hash change triggers regeneration
- **Benefit**: Fast reindexing (only changed files recomputed)

### Metadata Caching

- **Location**: `.filex/metadata/{hash}.json`
- **Key**: SHA256 hash of file path
- **Invalidation**: File hash change triggers regeneration
- **Benefit**: Fast status reporting without file I/O

### Search Index Caching

- **Location**: `.filex/index/search_index.npy` + `search_metadata.json`
- **Loading**: Loaded into memory on `SearchManager` initialization
- **Updates**: Saved to disk after each file indexing
- **Benefit**: Fast search queries (single NumPy operation)

## Performance Characteristics

### Indexing Performance

- **Text Files**: ~1-5 seconds per file (depends on size and model)
- **Image Files**: ~0.5-2 seconds per image (depends on model)
- **Batch Indexing**: Incremental updates ensure search remains available

### Search Performance

- **Query Embedding**: ~0.1-0.5 seconds (model inference)
- **Similarity Computation**: O(N) where N = number of chunks
- **Result Ranking**: O(N log N) for sorting
- **Typical Performance**: <1 second for repositories with thousands of chunks

### Storage Requirements

- **Embeddings**: ~3-4 KB per chunk (768 dimensions, float32)
- **Metadata**: ~200-500 bytes per file
- **Search Index**: Same as embeddings (in-memory copy)
- **Example**: 1000 chunks ≈ 3-4 MB embeddings + 200-500 KB metadata

## Data Consistency

### Change Detection

FileX uses three methods to detect file changes:
1. **File Hash**: SHA256 hash of file contents (most reliable)
2. **File Size**: Quick check for size changes
3. **Modification Time**: Fast check for timestamp changes

If any of these change, the file is reindexed.

### Search Index Consistency

- Search index is updated **immediately** after each file is indexed
- Old embeddings for a file are removed before adding new ones
- Search index is saved to disk after each update
- Ensures search results are always consistent with indexed files

### Model Consistency

- **Critical**: The same embedding model must be used for indexing and searching
- Mixing models produces incorrect results (different embedding spaces)
- FileX stores embedding dimensions in metadata to detect mismatches

## Extensibility

### Adding New File Types

1. Create new `FileHandler` implementation (e.g., `ImageFileHandler`)
2. Create new `Embedder` implementation (e.g., `CLIPImageEmbedder`)
3. Register handler in `FileProcessorRouter`
4. System automatically handles storage, indexing, and search

### Adding New Embedding Models

1. Implement `Embedder` interface
2. Configure model in `setup_components()`
3. System handles caching, storage, and search automatically

### Custom Chunking Strategies

1. Implement `Chunker` interface
2. Inject into `TextEmbeddingHandler`
3. System handles chunking, embedding, and storage automatically
