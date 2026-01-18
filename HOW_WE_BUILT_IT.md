# How We Built It

FileX was built for NWHacks 2026 as a comprehensive semantic file search system. Here's a detailed breakdown of the technologies, tools, and approaches we used:

## Architecture Overview

FileX follows a modular architecture with three main components:

1. **Backend (Python)**: Core indexing engine and semantic search with FastAPI web server
2. **Frontend (React/TypeScript)**: Modern web dashboard for visualization and interaction
3. **Repository System**: Git-like `.filex` directory structure for metadata storage

## Backend Technologies

### Core Libraries & Frameworks

**Semantic Search & Embeddings:**
- **sentence-transformers** (v2.2.0+): Powers text embedding generation using state-of-the-art Sentence-BERT models
  - Default model: `all-mpnet-base-v2` (768 dimensions) for high-quality semantic understanding
  - Alternative models: `all-MiniLM-L6-v2` (384 dims, faster), `paraphrase-multilingual-mpnet-base-v2` (multilingual)
- **transformers** (v4.30.0+): Hugging Face transformers library for model loading and management
- **torch** (v2.0.0+): PyTorch backend for neural network inference (required by sentence-transformers)
- **openai/clip-vit-base-patch32**: CLIP model for image embeddings (512 dimensions) via transformers

**Web Framework:**
- **FastAPI** (v0.104.0+): Modern, fast web framework for building the REST API
  - Automatic OpenAPI/Swagger documentation at `/docs`
  - Pydantic models for request/response validation
  - Background tasks for asynchronous indexing
- **uvicorn** (v0.24.0+): ASGI server for running FastAPI application
- **python-multipart** (v0.0.6+): Required for file upload handling

**Data Processing:**
- **numpy** (v1.24.0+): Vector operations for embeddings, cosine similarity calculations
  - Embeddings stored as NumPy arrays (`.npy` format) for efficient disk I/O
- **python-docx** (v1.1.0+): Extracts text content from Microsoft Word `.docx` files
- **Pillow** (v10.0.0+): Image processing for image embeddings (CLIP)

**Utilities:**
- **tqdm** (v4.65.0+): Progress bars for CLI indexing operations
- **typing-extensions** (v4.8.0+): Enhanced type hints for Python 3.9+ compatibility

### Backend Architecture Patterns

**Dependency Injection:**
- Protocol-based interfaces (`Embedder`, `Chunker`) defined in `interfaces.py`
- Concrete implementations (`SentenceTransformerEmbedder`, `FixedSizeChunker`) injected into handlers
- Enables easy swapping of embedding models or chunking strategies

**Repository Pattern:**
- `.filex/` directory structure mirrors Git's `.git/` approach
- Separate managers for different concerns:
  - `IndexManager`: Tracks file metadata, change detection via hashes
  - `StorageManager`: Handles embedding storage as NumPy arrays
  - `SearchManager`: Maintains in-memory search index with cosine similarity
  - `RepositoryManager`: Orchestrates all operations

**File Processing Pipeline:**
1. `FileProcessorRouter` determines file type (text/image/other)
2. Appropriate handler extracts content (`TextFileHandler` for `.txt/.docx`, `ImageFileHandler` for images)
3. `TextEmbeddingHandler` chunks content and generates embeddings
4. Embeddings stored on disk, search index updated incrementally

**Chunking Strategy:**
- `FixedSizeChunker`: Default 512 characters with 50-character overlap
- `SentenceAwareChunker`: Respects sentence boundaries (optional)
- Larger documents produce multiple embeddings for fine-grained search

## Frontend Technologies

### Core Stack

**Framework & Build Tools:**
- **React 18.3.1**: Modern React with hooks for component state management
- **TypeScript**: Full type safety across the frontend codebase
- **Vite 6.3.5**: Fast build tool and dev server with HMR (Hot Module Replacement)
- **@vitejs/plugin-react**: React plugin for Vite

**Styling:**
- **Tailwind CSS v4.1.12**: Utility-first CSS framework for rapid UI development
  - `@tailwindcss/vite`: Vite plugin for Tailwind
  - Dark mode support via CSS variables
- **class-variance-authority** (v0.7.1): Type-safe variant management for UI components
- **clsx** (v2.1.1) + **tailwind-merge** (v3.2.0): Conditional class merging utilities

**UI Component Library:**
- **Radix UI**: Comprehensive set of accessible, unstyled components:
  - `@radix-ui/react-dialog`, `@radix-ui/react-dropdown-menu`, `@radix-ui/react-tabs`
  - `@radix-ui/react-select`, `@radix-ui/react-progress`, `@radix-ui/react-tooltip`
  - Full accessibility (ARIA) support out of the box
  - 20+ Radix components used throughout the app

**Data Visualization:**
- **Recharts** (v2.15.2): React charting library built on D3.js
  - Used for: File type distribution pie charts, directory sizes, indexing activity timelines

**Icons & UI Utilities:**
- **lucide-react** (v0.487.0): Beautiful, consistent icon set (400+ icons)
- **next-themes** (v0.4.6): Dark mode theme provider with system preference detection
- **motion** (v12.23.24): Animation library for smooth transitions
- **date-fns** (v3.6.0): Date formatting utilities

**Additional Libraries:**
- **react-hook-form** (v7.55.0): Form state management
- **sonner** (v2.0.3): Toast notification system
- Various specialized UI libraries (carousel, calendar, command palette, etc.)

### Frontend Architecture

**Component Structure:**
```
src/
├── app/
│   ├── App.tsx                    # Main application component
│   ├── components/
│   │   ├── ui/                    # Reusable UI primitives (Radix-based)
│   │   ├── IndexingProgress.tsx   # Progress visualization
│   │   ├── FileTypeDistribution.tsx # Pie chart component
│   │   └── ...                    # Other dashboard components
│   ├── hooks/
│   │   └── useDirectoryData.ts    # Custom React hooks for data fetching
│   └── services/
│       └── dataService.ts         # API integration layer
```

**Data Flow:**
- `dataService.ts` abstracts API calls to FastAPI backend
- Custom hooks (`useDirectoryStats`) handle loading states and caching
- Components consume hooks and render with React Query-like patterns
- All components are fully typed with TypeScript

**State Management:**
- React hooks (`useState`, `useEffect`) for local component state
- Context API via `ThemeProvider` for global theme state
- API calls managed through async functions with loading/error states

## Development Tools & Practices

**Python:**
- `pyproject.toml`: Modern Python packaging (PEP 621) with setuptools backend
- Type hints throughout codebase for IDE support and documentation
- Structured logging via custom `logger.py` module
- Docstrings in Google/Javadoc style format

**TypeScript:**
- Strict type checking enabled
- Path aliases (`@/` -> `src/`) for clean imports
- Type definitions for all API responses

**Version Control:**
- Git repository with `.gitignore` for Python/Node artifacts
- `.filex/` directories excluded from version control (similar to `.git`)

## Key Design Decisions

**Why Sentence-BERT?**
- Optimized specifically for semantic similarity tasks
- Faster than full BERT while maintaining high quality
- 768-dimensional embeddings provide excellent semantic understanding
- Models cached locally after first download

**Why Separate Search Index?**
- In-memory index enables sub-millisecond search queries
- Index updates incrementally during indexing (no batch processing needed)
- Separates concerns: file tracking vs. search performance

**Why FastAPI?**
- Automatic API documentation
- Type validation via Pydantic
- Async support for background indexing tasks
- Fast performance comparable to Node.js

**Why Radix UI?**
- Accessibility built-in (WCAG compliant)
- Unstyled components allow full design control
- Smaller bundle size than Material UI or Ant Design
- Headless architecture aligns with Tailwind CSS approach

**Why Git-like Repository?**
- Familiar workflow for developers
- Each project can have its own `.filex` directory
- Repository discovered by walking up directory tree (like Git)
- Local-first approach ensures data privacy

## Performance Optimizations

**Backend:**
- Models loaded once at server startup, kept in memory
- Embeddings stored as binary NumPy arrays (efficient disk I/O)
- Change detection via file hashes (only re-index changed files)
- Background threading for indexing (non-blocking API)

**Frontend:**
- Vite for fast dev server and optimized production builds
- Code splitting via dynamic imports
- Lazy loading of charts (Recharts)
- Optimized asset bundling

## Security Considerations

- Server binds to `127.0.0.1` by default (localhost only)
- No authentication required (intended for local use)
- All data stored locally (no cloud sync)
- File paths validated before processing

## Hackathon Timeline & Approach

**Day 1: Core Infrastructure**
- Set up Python backend with sentence-transformers
- Implement basic file indexing and embedding generation
- Create `.filex` repository structure
- Build CLI interface (`filex.py`)

**Day 2: Search & Web API**
- Implement cosine similarity search
- Build FastAPI endpoints for search and indexing
- Add background task processing
- Create repository discovery system

**Day 3: Frontend Dashboard**
- Set up React + TypeScript + Vite project
- Integrate Radix UI components
- Build dashboard components (charts, progress bars)
- Connect frontend to FastAPI backend

**Day 4: Polish & Testing**
- Add image support (CLIP embeddings)
- Implement dark mode
- Add error handling and logging
- Test with real file collections
- Write documentation

## Challenges Overcome

1. **Model Loading Time**: Addressed by loading models once at startup and keeping in memory
2. **Large File Handling**: Implemented chunking strategy to break documents into manageable pieces
3. **Real-time Updates**: Used background threads and progress tracking endpoints
4. **Type Safety**: Comprehensive TypeScript types for frontend, type hints for Python backend
5. **Cross-platform Paths**: Used `pathlib.Path` in Python for Windows/Unix compatibility

## Future Enhancements

- Additional file type support (PDF, Markdown, code files)
- Full-text search combined with semantic search
- WebSocket support for real-time indexing progress
- Plugin system for custom embedders
- Distributed indexing for large file systems
