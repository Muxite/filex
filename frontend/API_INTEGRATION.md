# FileX Frontend API Integration

The frontend is now fully integrated with the FileX FastAPI backend.

## Setup

1. **Start the backend server**:
   ```bash
   cd backend
   python filex-web.py
   ```
   The API will be available at `http://127.0.0.1:8000`

2. **Start the frontend development server**:
   ```bash
   cd frontend
   npm install  # or pnpm install
   npm run dev  # or pnpm dev
   ```
   The frontend will be available at `http://localhost:5173` (or another port if 5173 is taken)

3. **Configure API URL** (optional):
   If your backend is running on a different host/port, create a `.env` file in the `frontend` directory:
   ```
   VITE_API_URL=http://127.0.0.1:8000
   ```

## Features

### Repository Management
- **List Repositories**: Automatically discovers all `.filex` repositories
- **Select Repository**: Choose which repository to view statistics for
- **Repository Stats**: View detailed statistics about indexed files

### Indexing
- **Index Files**: Start indexing files in the selected repository
- **Force Index All**: Force re-index all files (useful after model updates)
- **Progress Tracking**: Real-time progress updates during indexing
- **Auto-refresh**: Statistics automatically refresh when indexing completes

### Search
- **Semantic Search**: Search files using natural language queries
- **Search Results**: View file paths, chunk text, and similarity scores
- **Image Results**: Optionally include image previews in search results
- **Enter to Search**: Press Enter in the search box to search

### Statistics
- **File Type Distribution**: See breakdown of files by type
- **Storage Overview**: View storage usage and file counts
- **Indexing Progress**: Track indexing progress with real-time updates
- **Directory Sizes**: See which file types take up the most space

## API Endpoints Used

The frontend uses the following API endpoints:

- `GET /api/repositories` - List all available repositories
- `POST /api/stats` - Get repository statistics
- `POST /api/index` - Start indexing files
- `POST /api/search` - Search indexed files
- `GET /api/progress/{repo_id}` - Get indexing progress

## Data Flow

1. **Initial Load**:
   - Frontend fetches list of repositories
   - User selects a repository
   - Frontend fetches statistics for selected repository

2. **Indexing**:
   - User clicks "Index" or "Force Index All"
   - Frontend sends request to `/api/index`
   - Frontend polls `/api/progress/{repo_id}` every second
   - Statistics refresh automatically when indexing completes

3. **Search**:
   - User enters search query and clicks "Search" or presses Enter
   - Frontend sends request to `/api/search`
   - Results are displayed with file paths, chunk text, and similarity scores

4. **Real-time Updates**:
   - Statistics automatically refresh every 2 seconds when indexing is in progress
   - Progress updates show current indexed/total files count

## Error Handling

The frontend handles API errors gracefully:
- Network errors are logged to console
- User-friendly error messages are displayed
- Failed requests don't crash the application

## Development Notes

- The frontend uses React hooks for state management
- API calls are made through the `dataService` module
- All API responses are mapped to frontend data structures
- Progress polling automatically stops when indexing completes
