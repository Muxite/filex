# FileX Web API Documentation

The FileX Web API provides a RESTful interface for indexing and searching files using semantic embeddings. The server loads embedding models once at startup and keeps them in memory for fast responses.

## Starting the Server

```bash
python filex-web.py [--host HOST] [--port PORT]
```

**Default**: `http://127.0.0.1:8000` (localhost only, for security)

**Options**:
- `--host`: Host to bind to (default: 127.0.0.1)
- `--port`: Port to bind to (default: 8000)
- `--reload`: Enable auto-reload for development

**Example**:
```bash
python filex-web.py --host 127.0.0.1 --port 8000
```

The server will be available at:
- API: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`
- Alternative docs: `http://127.0.0.1:8000/redoc`

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running. The server will clean up resources and shut down gracefully.

## API Endpoints

### 1. List Repositories

**GET** `/api/repositories?start_path=...`

List all available `.filex` repositories.

**Query Parameters**:
- `start_path` (optional): Starting path for search (default: current directory)

**Response**:
```json
{
  "repositories": [
    {
      "repo_path": "/path/to/.filex",
      "work_tree": "/path/to",
      "name": "project_name"
    }
  ],
  "count": 1
}
```

### 2. Index Files

**POST** `/api/index`

Index files in a repository. Indexing runs in the background, allowing the API to respond immediately.

**Request Body**:
```json
{
  "repo_path": "/path/to/repository",  // Optional: if not provided, searches from current dir
  "path": "/path/to/file_or_dir",      // Optional: if not provided, indexes all files
  "force": false,                       // Force reindexing even if unchanged
  "recursive": true,                    // Recursively index subdirectories
  "extensions": [".txt", ".docx"]       // Optional: only index these extensions
}
```

**Response**:
```json
{
  "task_id": "/path/to/.filex",
  "status": "started",
  "message": "Indexing started in background"
}
```

**Note**: Use the `task_id` to check progress via `/api/progress/{task_id}`.

### 3. Search Files

**POST** `/api/search`

Search indexed files using natural language queries.

**Request Body**:
```json
{
  "repo_path": "/path/to/repository",  // Optional
  "query": "types of fruits",            // Search query text
  "top_k": 10,                          // Number of results (1-100)
  "include_images": false,              // Include image data in results
  "max_image_size_mb": 1.0              // Max image size to include (0.1-10.0 MB)
}
```

**Response**:
```json
{
  "query": "types of fruits",
  "results": [
    {
      "file_path": "/path/to/file.txt",
      "file_name": "file.txt",
      "chunk_index": 0,
      "chunk_text": "Apples, bananas, oranges...",
      "similarity_score": 0.8542,
      "image_data": "data:image/png;base64,...",  // Only if include_images=true
      "image_size_mb": 0.5                         // Only if include_images=true
    }
  ],
  "count": 10
}
```

### 4. Get Statistics

**POST** `/api/stats`

Get detailed statistics about a repository.

**Request Body**:
```json
{
  "repo_path": "/path/to/repository"  // Optional
}
```

**Response**:
```json
{
  "repository_path": "/path/to/.filex",
  "work_tree": "/path/to",
  "index_statistics": {
    "total_indexed_files": 100,
    "text_files": 80,
    "image_files": 20,
    "non_text_files": 20,
    "total_chunks": 500
  },
  "search_statistics": {
    "total_chunks": 500,
    "unique_files": 100,
    "embedding_dimension": 768
  },
  "storage_statistics": {
    "embeddings_bytes": 1536000,
    "embeddings_mb": 1.46,
    "metadata_bytes": 51200,
    "metadata_kb": 50.0,
    "total_bytes": 1587200,
    "total_mb": 1.51
  },
  "file_types": {
    ".txt": {
      "count": 50,
      "total_size": 1024000,
      "total_chunks": 250
    },
    ".png": {
      "count": 10,
      "total_size": 5120000,
      "total_chunks": 10
    }
  },
  "eligible_files_count": 150
}
```

### 5. Get Progress

**GET** `/api/progress/{repo_id}`

Get indexing progress for a repository. The `repo_id` is the repository path (same as `task_id` from index response).

**Response**:
```json
{
  "status": "indexing",  // "starting", "indexing", "completed", "error"
  "indexed": 50,
  "total": 100,
  "errors": 0
}
```

### 6. Clear Progress

**DELETE** `/api/progress/{repo_id}`

Clear completed indexing progress for a repository.

**Response**:
```json
{
  "message": "Progress cleared"
}
```

## Multiple Repositories

FileX supports multiple `.filex` repositories. Each repository is independent:

1. Use `/api/repositories` to discover all repositories
2. Specify `repo_path` in API requests to target a specific repository
3. Each repository maintains its own index, embeddings, and search data

## Example Usage

### Using curl

```bash
# List repositories
curl http://127.0.0.1:8000/api/repositories

# Index all files in a repository
curl -X POST http://127.0.0.1:8000/api/index \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/path/to/repository",
    "force": false,
    "recursive": true
  }'

# Check indexing progress
curl http://127.0.0.1:8000/api/progress/%2Fpath%2Fto%2F.filex

# Search files
curl -X POST http://127.0.0.1:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/path/to/repository",
    "query": "types of fruits",
    "top_k": 5
  }'

# Get statistics
curl -X POST http://127.0.0.1:8000/api/stats \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/path/to/repository"
  }'
```

### Using Python

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# List repositories
repos = requests.get(f"{BASE_URL}/api/repositories").json()
print(f"Found {repos['count']} repositories")

# Index files
response = requests.post(
    f"{BASE_URL}/api/index",
    json={
        "repo_path": "/path/to/repository",
        "force": False,
        "recursive": True
    }
)
task_id = response.json()["task_id"]

# Check progress
progress = requests.get(f"{BASE_URL}/api/progress/{task_id}").json()
print(f"Indexed: {progress['indexed']}/{progress['total']}")

# Search
results = requests.post(
    f"{BASE_URL}/api/search",
    json={
        "repo_path": "/path/to/repository",
        "query": "types of fruits",
        "top_k": 10
    }
).json()
print(f"Found {results['count']} results")

# Get statistics
stats = requests.post(
    f"{BASE_URL}/api/stats",
    json={"repo_path": "/path/to/repository"}
).json()
print(f"Total files: {stats['index_statistics']['total_indexed_files']}")
```

## Architecture

### Model Loading

- Models are loaded **once** at server startup (or on first request)
- Models remain in memory for the lifetime of the server
- This enables fast API responses without model loading overhead

### Asynchronous Indexing

- Indexing runs in background threads (not blocking API requests)
- Progress is tracked and can be queried via `/api/progress/{repo_id}`
- Multiple indexing tasks can run concurrently for different repositories

### Memory Management

- Image data in search results is optional and memory-constrained
- `max_image_size_mb` parameter limits image data size
- Large images are excluded from results to prevent memory issues

## Security Notes

- The server binds to `127.0.0.1` by default (localhost only)
- This prevents external access to your file system
- For production use, consider adding authentication and HTTPS

## Performance

- **Model Loading**: 5-10 seconds on first startup (models cached after first download)
- **Indexing**: ~1-5 seconds per file (depends on file size and model)
- **Search**: <1 second for repositories with thousands of chunks
- **API Response**: <100ms for most endpoints (after models are loaded)
