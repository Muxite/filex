"""
FastAPI web application for FileX indexing and search.
"""
import asyncio
import base64
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from concurrent.futures import ThreadPoolExecutor
import threading

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import (
    RepositoryManager,
    TextEmbeddingHandler,
    SentenceTransformerEmbedder,
    CLIPImageEmbedder,
    FixedSizeChunker,
    TextFileHandler,
    ImageFileHandler,
    FileProcessorRouter,
    Repository,
    IndexManager,
    StorageManager,
    SearchManager,
    SearchResult,
)


app = FastAPI(title="FileX Web API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GlobalState:
    """
    Global state for loaded models and managers.
    
    Models are loaded once and kept in memory for the lifetime of the server.
    """
    def __init__(self):
        self.text_embedder: Optional[SentenceTransformerEmbedder] = None
        self.image_embedder: Optional[CLIPImageEmbedder] = None
        self.text_embedding_handler: Optional[TextEmbeddingHandler] = None
        self.text_handler: Optional[TextFileHandler] = None
        self.image_handler: Optional[ImageFileHandler] = None
        self.processor: Optional[FileProcessorRouter] = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.indexing_tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
    
    def initialize_models(
        self,
        text_model: str = "all-mpnet-base-v2",
        image_model: str = "openai/clip-vit-base-patch32"
    ) -> None:
        """
        Initialize embedding models (called once at startup).
        
        :param text_model: Sentence-transformer model name
        :param image_model: CLIP model name
        """
        if self.text_embedder is None:
            self.text_embedder = SentenceTransformerEmbedder(model_name=text_model)
            chunker = FixedSizeChunker(chunk_size=512, overlap=50)
            self.text_embedding_handler = TextEmbeddingHandler(
                embedder=self.text_embedder,
                chunker=chunker
            )
            self.text_handler = TextFileHandler(embedding_handler=self.text_embedding_handler)
        
        if self.image_embedder is None:
            try:
                self.image_embedder = CLIPImageEmbedder(model_name=image_model)
                self.image_handler = ImageFileHandler(image_embedder=self.image_embedder)
            except Exception as e:
                print(f"Warning: Could not initialize image handler: {e}")
                self.image_handler = None
        
        if self.processor is None:
            if self.image_handler:
                self.processor = FileProcessorRouter(
                    text_handler=self.text_handler,
                    image_handler=self.image_handler
                )
            else:
                self.processor = FileProcessorRouter(text_handler=self.text_handler)
    
    def get_repo_manager(self, repo_path: Optional[str] = None) -> RepositoryManager:
        """
        Get or create RepositoryManager for a specific repository.
        
        :param repo_path: Path to directory where .filex should be created/used
                         If path doesn't have .filex, it will be created
        :returns: RepositoryManager instance
        :raises ValueError: If path does not exist or is not a directory
        """
        if self.processor is None:
            self.initialize_models()
        
        if repo_path:
            try:
                path = Path(repo_path).resolve()
            except Exception as e:
                raise ValueError(f"Invalid path format: {repo_path} - {str(e)}")
            
            if not path.exists():
                raise ValueError(f"Path does not exist: {repo_path}")
            if not path.is_dir():
                raise ValueError(f"Path is not a directory: {repo_path}")
            
            return RepositoryManager(start_path=str(path), processor=self.processor, create=True)
        else:
            return RepositoryManager(processor=self.processor, create=True)
    
    def cleanup(self) -> None:
        """
        Clean up resources.
        """
        try:
            # Shutdown executor without waiting for tasks to complete
            # This allows Ctrl+C to work immediately
            # cancel_futures is only available in Python 3.9+
            import sys
            if sys.version_info >= (3, 9):
                self.executor.shutdown(wait=False, cancel_futures=True)
            else:
                self.executor.shutdown(wait=False)
        except Exception as e:
            print(f"Error during cleanup: {e}")


state = GlobalState()


class IndexRequest(BaseModel):
    repo_path: Optional[str] = Field(None, description="Path to repository root (if None, uses current directory)")
    path: Optional[str] = Field(None, description="File or directory to index (if None, indexes all files)")
    force: bool = Field(False, description="Force reindexing even if files haven't changed")
    recursive: bool = Field(True, description="Recursively index subdirectories")
    extensions: Optional[List[str]] = Field(None, description="Only index files with these extensions")


class SearchRequest(BaseModel):
    repo_path: Optional[str] = Field(None, description="Path to repository root")
    query: str = Field(..., description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    include_images: bool = Field(False, description="Include image data in results (memory constrained)")
    max_image_size_mb: float = Field(1.0, ge=0.1, le=10.0, description="Maximum image size in MB")


class RepoPathRequest(BaseModel):
    repo_path: Optional[str] = Field(None, description="Path to repository root")


class RegisterFolderRequest(BaseModel):
    path: str = Field(..., description="Path to folder to register")




@app.on_event("startup")
async def startup_event():
    """
    Initialize models on startup.
    """
    print("Initializing FileX models (this may take a few seconds)...")
    state.initialize_models()
    print("FileX models loaded and ready.")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on shutdown.
    """
    try:
        state.cleanup()
        # Flush all logging handlers
        import logging
        for handler in logging.root.handlers[:]:
            handler.flush()
            if hasattr(handler, 'close'):
                handler.close()
    except Exception as e:
        print(f"Error during shutdown: {e}")
    finally:
        print("FileX server shutdown complete.")


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "FileX Web API",
        "version": "1.0.0",
        "endpoints": {
            "repositories": "/api/repositories",
            "index": "/api/index",
            "search": "/api/search",
            "stats": "/api/stats",
            "progress": "/api/progress",
        }
    }


REGISTERED_FOLDERS_FILE = Path(__file__).parent.parent / "registered_folders.json"


def load_registered_folders() -> List[str]:
    """
    Load registered folders from JSON file.
    
    :returns: List of folder paths
    """
    try:
        if REGISTERED_FOLDERS_FILE.exists():
            with open(REGISTERED_FOLDERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("folders", [])
        return []
    except Exception as e:
        print(f"Error loading registered folders: {e}")
        return []


def save_registered_folders(folders: List[str]) -> None:
    """
    Save registered folders to JSON file.
    
    :param folders: List of folder paths to save
    """
    try:
        REGISTERED_FOLDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTERED_FOLDERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"folders": folders}, f, indent=2)
    except Exception as e:
        print(f"Error saving registered folders: {e}")
        raise


@app.get("/api/repositories")
async def list_repositories():
    """
    List recently used .filex repositories.
    
    Returns empty list - repositories are managed by user-provided paths.
    
    :returns: List of repository information (currently empty)
    """
    return {"repositories": [], "count": 0}


@app.get("/api/registered-folders")
async def get_registered_folders():
    """
    Get list of registered folders.
    
    :returns: List of registered folder paths
    """
    folders = load_registered_folders()
    return {"folders": folders, "count": len(folders)}


@app.post("/api/registered-folders")
async def register_folder(request: RegisterFolderRequest):
    """
    Register a new folder path.
    
    :param request: Folder path to register
    :returns: Success message and updated folder list
    """
    try:
        path = Path(request.path).resolve()
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Path does not exist: {request.path}")
        if not path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.path}")
        
        folders = load_registered_folders()
        path_str = str(path)
        
        if path_str not in folders:
            folders.append(path_str)
            save_registered_folders(folders)
        
        return {"message": "Folder registered successfully", "folders": folders, "count": len(folders)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register folder: {str(e)}")


@app.delete("/api/registered-folders/{folder_path:path}")
async def unregister_folder(folder_path: str):
    """
    Unregister a folder path.
    
    :param folder_path: Path to folder to unregister (URL encoded)
    :returns: Success message and updated folder list
    """
    try:
        folders = load_registered_folders()
        path_str = str(Path(folder_path).resolve())
        
        if path_str in folders:
            folders.remove(path_str)
            save_registered_folders(folders)
        
        return {"message": "Folder unregistered successfully", "folders": folders, "count": len(folders)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unregister folder: {str(e)}")


@app.post("/api/index")
async def index_files(request: IndexRequest, background_tasks: BackgroundTasks):
    """
    Index files in a repository.
    
    :param request: Indexing request parameters
    :param background_tasks: FastAPI background tasks
    :returns: Task information
    """
    try:
        if not request.repo_path:
            raise HTTPException(status_code=400, detail="repo_path is required")
        
        # Validate path before creating repository manager
        try:
            path = Path(request.repo_path).resolve()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid path format: {str(e)}")
        
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Path does not exist: {request.repo_path}")
        
        if not path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.repo_path}")
        
        repo_manager = state.get_repo_manager(request.repo_path)
        repo_id = str(repo_manager.repository.repo_path)
        
        with state.lock:
            if repo_id in state.indexing_tasks:
                existing_task = state.indexing_tasks[repo_id]
                if existing_task["status"] in ("starting", "indexing"):
                    return JSONResponse(
                        status_code=409,
                        content={
                            "error": "Indexing already in progress for this repository",
                            "task_id": repo_id,
                            "status": existing_task["status"],
                            "indexed": existing_task.get("indexed", 0),
                            "total": existing_task.get("total", 0),
                        }
                    )
            
            state.indexing_tasks[repo_id] = {
                "status": "starting",
                "indexed": 0,
                "total": 0,
                "errors": 0,
                "message": "Initializing indexing...",
            }
        
        def index_task():
            try:
                with state.lock:
                    state.indexing_tasks[repo_id]["status"] = "indexing"
                    state.indexing_tasks[repo_id]["message"] = "Indexing files..."
                
                if request.path:
                    path = Path(request.path)
                    if path.is_file():
                        result = repo_manager.index_file(str(path), force=request.force)
                        with state.lock:
                            if result.get("indexed"):
                                state.indexing_tasks[repo_id]["indexed"] = 1
                                state.indexing_tasks[repo_id]["total"] = 1
                                state.indexing_tasks[repo_id]["message"] = "File indexed successfully"
                            else:
                                state.indexing_tasks[repo_id]["indexed"] = 0
                                state.indexing_tasks[repo_id]["total"] = 1
                                state.indexing_tasks[repo_id]["message"] = "File skipped (unchanged)"
                    else:
                        default_indexable_extensions = ['.txt', '.docx', '.png', '.jpg', '.jpeg']
                        extensions_to_use = request.extensions if request.extensions is not None else default_indexable_extensions
                        stats = repo_manager.index_directory(
                            directory=request.path,
                            recursive=request.recursive,
                            extensions=extensions_to_use,
                            force=request.force,
                        )
                        with state.lock:
                            state.indexing_tasks[repo_id]["indexed"] = stats["indexed"]
                            state.indexing_tasks[repo_id]["total"] = stats["total_files"]
                            state.indexing_tasks[repo_id]["errors"] = stats["errors"]
                            state.indexing_tasks[repo_id]["message"] = f"Indexed {stats['indexed']} of {stats['total_files']} files"
                else:
                    default_indexable_extensions = ['.txt', '.docx', '.png', '.jpg', '.jpeg']
                    extensions_to_use = request.extensions if request.extensions is not None else default_indexable_extensions
                    stats = repo_manager.index_directory(
                        recursive=request.recursive,
                        extensions=extensions_to_use,
                        force=request.force,
                    )
                    with state.lock:
                        state.indexing_tasks[repo_id]["indexed"] = stats["indexed"]
                        state.indexing_tasks[repo_id]["total"] = stats["total_files"]
                        state.indexing_tasks[repo_id]["errors"] = stats["errors"]
                        state.indexing_tasks[repo_id]["message"] = f"Indexed {stats['indexed']} of {stats['total_files']} files"
                
                with state.lock:
                    state.indexing_tasks[repo_id]["status"] = "completed"
                    state.indexing_tasks[repo_id]["message"] = "Indexing completed successfully"
            except Exception as e:
                with state.lock:
                    state.indexing_tasks[repo_id]["status"] = "error"
                    state.indexing_tasks[repo_id]["error"] = str(e)
                    state.indexing_tasks[repo_id]["message"] = f"Indexing failed: {str(e)}"
        
        state.executor.submit(index_task)
        
        return {
            "task_id": repo_id,
            "status": "started",
            "message": "Indexing started in background",
            "repo_path": request.repo_path,
        }
    except HTTPException:
        raise
    except ValueError as e:
        # Convert ValueError to HTTPException for path validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start indexing: {str(e)}")


@app.post("/api/search")
async def search_files(request: SearchRequest):
    """
    Search indexed files.
    
    :param request: Search request parameters
    :returns: Search results with file locations and text
    """
    try:
        repo_manager = state.get_repo_manager(request.repo_path)
        search_manager = repo_manager.search_manager
        
        if state.text_embedding_handler is None:
            raise HTTPException(status_code=500, detail="Text embedding handler not initialized")
        
        _, query_embedding = state.text_embedding_handler.embed_text(request.query)
        if query_embedding.ndim > 1 and query_embedding.shape[0] == 1:
            query_embedding = query_embedding[0]
        
        image_query_embedding = None
        if state.image_embedder is not None:
            try:
                image_query_embedding = state.image_embedder.embed_text(request.query)
            except Exception as e:
                print(f"Warning: Failed to generate image query embedding: {e}")
        
        results = search_manager.search(
            query_embedding,
            top_k=request.top_k,
            image_query_embedding=image_query_embedding,
        )
        
        formatted_results = []
        for result in results:
            result_data = {
                "file_path": result.file_path,
                "file_name": result.file_name,
                "chunk_index": result.chunk_index,
                "chunk_text": result.chunk_text,
                "similarity_score": float(result.similarity_score),
            }
            
            if request.include_images:
                file_path = Path(result.file_path)
                if file_path.exists() and file_path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    if file_size_mb <= request.max_image_size_mb:
                        try:
                            with open(file_path, 'rb') as f:
                                image_data = f.read()
                                image_base64 = base64.b64encode(image_data).decode('utf-8')
                                result_data["image_data"] = f"data:image/{file_path.suffix[1:]};base64,{image_base64}"
                                result_data["image_size_mb"] = file_size_mb
                        except Exception as e:
                            result_data["image_error"] = str(e)
            
            formatted_results.append(result_data)
        
        return {
            "query": request.query,
            "results": formatted_results,
            "count": len(formatted_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stats")
async def get_stats(request: RepoPathRequest):
    """
    Get repository statistics.
    
    Creates repository if it doesn't exist. Provides approximate stats
    for directories that haven't been indexed yet.
    
    :param request: Repository path request
    :returns: Detailed statistics about the repository
    """
    try:
        work_tree_path = None
        if request.repo_path:
            path = Path(request.repo_path).resolve()
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"Path does not exist: {request.repo_path}")
            if not path.is_dir():
                raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.repo_path}")
            work_tree_path = path
        
        repo_manager = state.get_repo_manager(request.repo_path)
        index_manager = repo_manager.index_manager
        storage_manager = repo_manager.storage_manager
        search_manager = repo_manager.search_manager
        work_tree = repo_manager.repository.get_work_tree_root()
        
        entries = index_manager.get_all_entries()
        storage_size = storage_manager.get_storage_size()
        search_stats = search_manager.get_index_stats()
        
        file_types = {}
        for entry in entries:
            ext = entry.extension.lower()
            if ext not in file_types:
                file_types[ext] = {"count": 0, "total_size": 0, "total_chunks": 0}
            file_types[ext]["count"] += 1
            file_types[ext]["total_size"] += entry.file_size
            if entry.num_chunks:
                file_types[ext]["total_chunks"] += entry.num_chunks
        
        text_files = sum(1 for e in entries if e.is_text_type)
        image_extensions = {'.png', '.jpg', '.jpeg'}
        image_files = sum(1 for e in entries if e.extension.lower() in image_extensions)
        non_text_files = len(entries) - text_files
        total_chunks = sum(e.num_chunks or 0 for e in entries)
        
        eligible_files = []
        eligible_file_types = {}
        text_extensions = {'.txt', '.docx'}
        indexable_extensions = {'.txt', '.docx', '.png', '.jpg', '.jpeg'}
        total_size = 0
        
        for file_path in work_tree.rglob("*"):
            if file_path.is_file() and ".filex" not in file_path.parts:
                ext = file_path.suffix.lower()
                if ext in indexable_extensions:
                    eligible_files.append(str(file_path))
                    if ext not in eligible_file_types:
                        eligible_file_types[ext] = {"count": 0, "total_size": 0}
                    eligible_file_types[ext]["count"] += 1
                    try:
                        file_size = file_path.stat().st_size
                        eligible_file_types[ext]["total_size"] += file_size
                        total_size += file_size
                    except:
                        pass
        
        eligible_text_files = sum(1 for f in eligible_files if Path(f).suffix.lower() in text_extensions)
        eligible_image_files = sum(1 for f in eligible_files if Path(f).suffix.lower() in image_extensions)
        
        return {
            "repository_path": str(repo_manager.repository.repo_path),
            "work_tree": str(work_tree),
            "index_statistics": {
                "total_indexed_files": len(entries),
                "text_files": text_files,
                "image_files": image_files,
                "non_text_files": non_text_files,
                "total_chunks": total_chunks,
            },
            "search_statistics": {
                "total_chunks": search_stats["total_chunks"],
                "unique_files": search_stats["unique_files"],
                "embedding_dimension": search_stats["embedding_dimension"],
            },
            "storage_statistics": {
                "embeddings_bytes": storage_size["embeddings_bytes"],
                "embeddings_mb": storage_size["embeddings_bytes"] / (1024 * 1024),
                "metadata_bytes": storage_size["metadata_bytes"],
                "metadata_kb": storage_size["metadata_bytes"] / 1024,
                "total_bytes": storage_size["total_bytes"],
                "total_mb": storage_size["total_bytes"] / (1024 * 1024),
            },
            "file_types": file_types,
            "eligible_files_count": len(eligible_files),
            "eligible_file_types": eligible_file_types,
            "eligible_statistics": {
                "total_files": len(eligible_files),
                "text_files": eligible_text_files,
                "image_files": eligible_image_files,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/progress/{repo_id}")
async def get_progress(repo_id: str):
    """
    Get indexing progress for a repository.
    
    :param repo_id: Repository path (used as task ID, URL encoded)
    :returns: Current indexing progress
    """
    try:
        decoded_repo_id = repo_id
        with state.lock:
            if decoded_repo_id not in state.indexing_tasks:
                return {
                    "status": "not_found",
                    "indexed": 0,
                    "total": 0,
                    "errors": 0,
                    "message": "No indexing task found"
                }
            
            task_info = state.indexing_tasks[decoded_repo_id].copy()
        
        return task_info
    except Exception as e:
        return {
            "status": "error",
            "indexed": 0,
            "total": 0,
            "errors": 0,
            "message": f"Error getting progress: {str(e)}"
        }


@app.delete("/api/progress/{repo_id}")
async def clear_progress(repo_id: str):
    """
    Clear completed indexing progress for a repository.
    
    :param repo_id: Repository path (used as task ID)
    :returns: Success message
    """
    with state.lock:
        if repo_id in state.indexing_tasks:
            task = state.indexing_tasks[repo_id]
            if task["status"] in ("completed", "error"):
                del state.indexing_tasks[repo_id]
                return {"message": "Progress cleared"}
            else:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Cannot clear progress for active indexing task"}
                )
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "No progress found for this repository"}
            )
