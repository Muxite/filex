# filex
Google search for your file system. NWHacks 2026 
A local service that indexes and analyses a directory so that users can search a variety of files semantically based on document content (ex: `.txt`, `.docx` `.c`) and also image content (`.png`, `.jpg`, `.webp`). 
It uses a combination of text embeddings, large language models, and computer vision to generate its metadata to track files. 
A website is included to allow users to access their system efficiently, running locally for security.

## MVP Status

### Completed: Full-Featured CLI Tool for Semantic File Indexing and Search

FileX now includes a complete, production-ready command-line interface that transforms how you search through your files. The system uses state-of-the-art semantic search technology to understand the meaning of your documents, not just keywords.

**What's Working Right Now:**

**Powerful Indexing System**
- Intelligent file indexing that automatically detects changes and only re-indexes what's needed
- Support for `.txt` and `.docx` files with automatic text extraction
- Recursive directory scanning with configurable file type filtering
- Smart change detection using file hashes, sizes, and modification times
- Progress tracking with real-time progress bars showing indexing status

**Advanced Semantic Search**
- Natural language queries - search using plain English, not just keywords
- High-dimensional embeddings (768 dimensions) for superior semantic understanding
- Configurable embedding models - choose the right balance of speed and quality
- Real-time search index that updates immediately as files are indexed
- Cosine similarity search for finding semantically related content
- Flexible query syntax with result count controls

**Robust Repository Management**
- Git-like repository system with `.filex` directory for metadata storage
- Automatic repository discovery by walking up the directory tree
- Separate storage for embeddings, metadata, and search indices
- Comprehensive status reporting with detailed statistics
- Efficient storage using NumPy arrays and JSON metadata

**Performance Optimizations**
- Model caching - embedding models are cached after first download
- Incremental updates - search index updates after each file, not in batches
- Fast status command that doesn't require model loading
- Optimized embedding generation with batch processing support

**Usage:**
```bash
# Index all files in the current repository
python filex.py index

# Index a specific file or directory
python filex.py index path/to/file.txt
python filex.py index path/to/directory

# Search with natural language
python filex.py search "types of fruits"
python filex.py search "programming languages" --count 5

# Check repository status
python filex.py status
```

### Planned Features

**Web API Endpoints**
- RESTful API for file upload and indexing
- HTTP endpoints for search functionality
- Web-based user interface for file management

**Image Support**
- Computer vision integration for `.png`, `.jpg`, `.webp` files
- Multimodal embeddings combining text and image understanding

## Embedding Models & Techniques

FileX leverages cutting-edge high-dimensional embedding technology to transform your files into searchable vector representations. The system supports multiple state-of-the-art embedding models, each optimized for different performance and quality requirements.

### Supported Embedding Models

| Model Name | Embedding Dimension | Technique Type | Strengths | When to Use |
|---|---|---|---|---|
| **all-mpnet-base-v2** (Default) | 768 | Sentence-BERT (Transformer-based) | High-quality semantic understanding, contextual embeddings, best for semantic similarity | Recommended default for most use cases, especially semantic search and document similarity |
| **all-MiniLM-L12-v2** | 384 | Sentence-BERT (Lightweight) | Faster inference, good quality, lower memory usage | When speed is important and quality can be slightly reduced |
| **all-MiniLM-L6-v2** | 384 | Sentence-BERT (Ultra-lightweight) | Fastest inference, smallest model size | For quick prototyping or resource-constrained environments |
| **paraphrase-multilingual-mpnet-base-v2** | 768 | Multilingual Sentence-BERT | Supports 50+ languages, high quality | When indexing multilingual documents |
| **sentence-transformers/all-roberta-large-v1** | 1024 | RoBERTa-based (Large) | Highest quality, best semantic understanding | When maximum search quality is required and resources allow |

### Embedding Techniques Explained

#### 1. Sentence-BERT (SBERT)
**What it is**: A modification of the BERT model that produces semantically meaningful sentence embeddings suitable for similarity tasks.

**How it works**: 
- Uses siamese and triplet network structures
- Fine-tuned on semantic similarity tasks
- Generates fixed-size embeddings (typically 384-768 dimensions)
- Optimized for cosine similarity and semantic search

**Usage in FileX**: Default technique for all text-based file indexing and search. Converts document chunks and search queries into high-dimensional vectors in the same embedding space.

#### 2. Contextual Word Embeddings (Transformer-based)
**What it is**: Embeddings that capture word meaning based on context, unlike static word embeddings.

**How it works**:
- Uses transformer architecture (attention mechanisms)
- Processes full context of sentences/documents
- Handles polysemy (words with multiple meanings)
- Generates embeddings that vary based on surrounding text

**Usage in FileX**: The underlying technology for Sentence-BERT models, enabling understanding of context and meaning rather than just keyword matching.

#### 3. Semantic Similarity Search
**What it is**: Finding documents based on meaning and semantic similarity rather than exact keyword matches.

**How it works**:
- Documents and queries are embedded into the same vector space
- Cosine similarity is computed between query and document embeddings
- Results are ranked by semantic similarity scores
- Enables finding relevant content even without exact keyword matches

**Usage in FileX**: Core search mechanism - users can search with natural language queries and find relevant content based on meaning.

### Model Selection Guidelines

**For Production Use**:
- **Default**: `all-mpnet-base-v2` (768 dimensions) - Best balance of quality and performance
- **High Quality**: `all-roberta-large-v1` (1024 dimensions) - Maximum search accuracy
- **Multilingual**: `paraphrase-multilingual-mpnet-base-v2` (768 dimensions) - For non-English content

**For Development/Testing**:
- **Fast**: `all-MiniLM-L6-v2` (384 dimensions) - Quick iteration and testing
- **Balanced**: `all-MiniLM-L12-v2` (384 dimensions) - Good quality with better speed

### Using Different Models

Specify the embedding model when indexing or searching:

```bash
# Index with default model (all-mpnet-base-v2, 768 dimensions)
python filex.py index

# Index with a faster, lighter model
python filex.py index --model all-MiniLM-L6-v2

# Search with a specific model (must match indexing model)
python filex.py search "your query" --model all-mpnet-base-v2
```

**Important**: The model used for indexing must match the model used for searching. FileX stores embeddings in the repository, and mixing models will produce incorrect results.

### Embedding Dimensions & Performance

**Higher Dimensions (768-1024)**:
- Better semantic understanding
- More nuanced similarity matching
- Better handling of complex queries
- Higher memory usage
- Slower inference

**Lower Dimensions (384)**:
- Faster inference
- Lower memory usage
- Good for large-scale indexing
- Slightly reduced semantic quality
- May miss subtle semantic relationships

### Technical Details

- **Embedding Space**: All embeddings are normalized and use cosine similarity for comparison
- **Chunking**: Documents are split into chunks (default: 512 characters with 50 character overlap) before embedding
- **Storage**: Embeddings are stored as NumPy arrays in the `.filex/embeddings/` directory
- **Search Index**: Maintained separately from file index for efficient search operations
- **Incremental Updates**: Search index is updated immediately after each file is indexed

### Best Practices

1. **Consistency**: Always use the same model for indexing and searching
2. **Quality vs Speed**: Choose based on your use case - production should use higher-dimensional models
3. **Multilingual Content**: Use multilingual models when indexing documents in multiple languages
4. **Resource Constraints**: Use lighter models (384 dimensions) if memory or speed is a concern
5. **Model Caching**: Models are downloaded and cached automatically on first use

​​
