# FileDex

**Search by meaning, not filenames.**

Why is it easier to find a photo on Google than in your own files? Upgrade your system with FileDex!

FileDex is a powerful semantic search engine for your storage. Search your files using natural language, just like Google, with an efficient graphical user interface and command line interface. Find documents, images, and files by meaning, not just keywords. Completely local and secure, your data never leaves your device. 

[View on Devpost](https://devpost.com/software/filedex) | Made at NWHacks 2026

## Features

**Semantic Search**
- Search using natural language queries - find files by meaning, not just filenames
- Works with text documents (`.txt`, `.docx`) and images (`.png`, `.jpg`, `.webp`)
- Cross-modal search: find images by describing them in text

**Dual Interface**
- **Command Line**: Fast, scriptable CLI for power users
- **Web Dashboard**: Beautiful, interactive GUI with real-time statistics and visualizations

**Privacy-First**
- 100% local processing - no data leaves your device
- All embeddings and metadata stored locally in `.filex/` directories
- No cloud sync, no external services, complete data sovereignty

**Fast & Efficient**
- Git-like file tracking with automatic change detection
- Incremental indexing - only re-indexes what's changed
- Near-instant search results with in-memory similarity matching

**Smart Indexing**
- Automatic file type detection and content extraction
- Intelligent chunking for large documents
- Background processing keeps the UI responsive

## Quick Start

### Command Line Interface

```bash
# Index all files in the current directory
python filex.py index

# Search with natural language
python filex.py search "types of fruits"
python filex.py search "plane" --count 10

# Check repository status
python filex.py status
```

### Web Dashboard

```bash
# Start the web server
python filex-web.py

# Open http://127.0.0.1:8000 in your browser
```

The web interface provides:
- Visual search with real-time results
- Indexing progress tracking
- File type distribution charts
- Storage statistics
- Dark mode support

## How It Works

FileX uses AI embedding models to understand the semantic meaning of your files:

**Text Files**: Embedded using Sentence-Transformers (768-dimensional vectors) for semantic understanding. Documents are chunked intelligently to capture context while maintaining search performance.

**Images**: Embedded using OpenAI's CLIP ViT-B/32 model, enabling cross-modal search where text queries can find relevant images in the same embedding space.

**Search**: Both text and image embeddings are stored locally as NumPy arrays. An in-memory cosine similarity index enables near-instant search queries after initial indexing.

**Repository System**: Each directory can have its own `.filex/` repository (similar to Git's `.git/`), automatically tracking file changes and maintaining separate indices for efficient updates.

## Architecture

FileX is built with a modular architecture:

- **Backend**: Python/FastAPI server with background task processing
- **Frontend**: React/TypeScript dashboard with Tailwind CSS
- **Storage**: Local `.filex/` directories with NumPy array embeddings and JSON metadata
- **Search**: In-memory cosine similarity index for fast queries

See [HOW_WE_BUILT_IT.md](HOW_WE_BUILT_IT.md) for detailed technical information.

## Installation

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Usage Examples

### Indexing Files

```bash
# Index all files in repository
python filex.py index

# Index specific directory
python filex.py index path/to/directory

# Index only specific file types
python filex.py index --extensions .txt .docx .jpg

# Force re-index everything
python filex.py index --force
```

### Searching

```bash
# Basic search
python filex.py search "meeting notes"

# Limit results
python filex.py search "programming languages" --count 5

# Search with inline count
python filex.py search "types of fruits -count 10"
```

### Web API

The FastAPI server provides REST endpoints for programmatic access:

- `POST /api/index` - Index files
- `POST /api/search` - Search files
- `POST /api/stats` - Get repository statistics
- `GET /api/progress/{repo_id}` - Check indexing progress

See [backend/WEB_API.md](backend/WEB_API.md) for complete API documentation.

## Supported File Types

**Text Files**
- `.txt` - Plain text files
- `.docx` - Microsoft Word documents

**Images**
- `.png` - PNG images
- `.jpg`, `.jpeg` - JPEG images
- `.webp` - WebP images

Additional file types can be added by extending the file handlers.

## Embedding Models

FileX supports multiple embedding models optimized for different use cases:

| Model | Dimensions | Best For |
|-------|-----------|----------|
| `all-mpnet-base-v2` (Default) | 768 | Production use, best quality/speed balance |
| `all-MiniLM-L6-v2` | 384 | Fast indexing, resource-constrained environments |
| `paraphrase-multilingual-mpnet-base-v2` | 768 | Multilingual documents |

Specify models when indexing:
```bash
python filex.py index --model all-mpnet-base-v2
```

**Important**: Use the same model for indexing and searching.

## Privacy & Security

- **100% Local**: All processing happens on your machine
- **No Network**: No data is sent to external services
- **Local Storage**: All embeddings stored in `.filex/` directories
- **No Authentication Required**: Designed for local use only (server binds to localhost by default)

## Performance

- **Indexing**: ~1-5 seconds per file (depends on size and model)
- **Search**: <1 second for repositories with thousands of chunks
- **Model Loading**: 5-10 seconds on first run (cached after download)
- **Memory**: Models loaded once and kept in memory for fast responses

## What's Next

- Additional file type support (PDF, Markdown, code files)
- Full-text search combined with semantic search
- WebSocket support for real-time indexing progress
- Plugin system for custom embedders
- Distributed indexing for large file systems

## License

Made at NWHacks 2026.

---

**FileX** - The file explorer upgrade you never knew you needed. Simple, fast, and intuitive - just like Google, but for your files.
