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
        
        :param repo_path: Path to repository root (if None, searches from current dir)
        :returns: RepositoryManager instance
        """
        if self.processor is None:
            self.initialize_models()
        
        if repo_path:
            return RepositoryManager(start_path=repo_path, processor=self.processor, create=True)
        else:
            return RepositoryManager(processor=self.processor, create=True)
    
    def cleanup(self) -> None:
        """
        Clean up resources.
        """
        self.executor.shutdown(wait=True)


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


def find_all_repositories(start_path: str = ".") -> List[Dict[str, str]]:
    """
    Find all .filex repositories starting from a given path.
    
    :param start_path: Starting path for search
    :returns: List of repository info dictionaries
    """
    repos = []
    start = Path(start_path).resolve()
    
    for root, dirs, files in os.walk(start):
        if ".filex" in dirs:
            repo_path = Path(root) / ".filex"
            work_tree = Path(root)
            repos.append({
                "repo_path": str(repo_path),
                "work_tree": str(work_tree),
                "name": work_tree.name or str(work_tree)
            })
            dirs.remove(".filex")
    
    return repos


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
    state.cleanup()
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


@app.get("/api/repositories")
async def list_repositories(start_path: Optional[str] = None):
    """
    List all available .filex repositories.
    
    :param start_path: Starting path for search (default: current directory)
    :returns: List of repository information
    """
    if start_path is None:
        start_path = os.getcwd()
    
    repos = find_all_repositories(start_path)
    return {"repositories": repos, "count": len(repos)}


@app.post("/api/index")
async def index_files(request: IndexRequest, background_tasks: BackgroundTasks):
    """
    Index files in a repository.
    
    :param request: Indexing request parameters
    :param background_tasks: FastAPI background tasks
    :returns: Task information
    """
    try:
        repo_manager = state.get_repo_manager(request.repo_path)
        repo_id = str(repo_manager.repository.repo_path)
        
        with state.lock:
            if repo_id in state.indexing_tasks:
                return JSONResponse(
                    status_code=409,
                    content={"error": "Indexing already in progress for this repository"}
                )
            
            state.indexing_tasks[repo_id] = {
                "status": "starting",
                "indexed": 0,
                "total": 0,
                "errors": 0,
            }
        
        def index_task():
            try:
                with state.lock:
                    state.indexing_tasks[repo_id]["status"] = "indexing"
                
                if request.path:
                    path = Path(request.path)
                    if path.is_file():
                        result = repo_manager.index_file(str(path), force=request.force)
                        with state.lock:
                            if result.get("indexed"):
                                state.indexing_tasks[repo_id]["indexed"] = 1
                                state.indexing_tasks[repo_id]["total"] = 1
                            else:
                                state.indexing_tasks[repo_id]["indexed"] = 0
                                state.indexing_tasks[repo_id]["total"] = 1
                    else:
                        stats = repo_manager.index_directory(
                            directory=request.path,
                            recursive=request.recursive,
                            extensions=request.extensions,
                            force=request.force,
                        )
                        with state.lock:
                            state.indexing_tasks[repo_id]["indexed"] = stats["indexed"]
                            state.indexing_tasks[repo_id]["total"] = stats["total_files"]
                            state.indexing_tasks[repo_id]["errors"] = stats["errors"]
                else:
                    stats = repo_manager.index_directory(
                        recursive=request.recursive,
                        extensions=request.extensions,
                        force=request.force,
                    )
                    with state.lock:
                        state.indexing_tasks[repo_id]["indexed"] = stats["indexed"]
                        state.indexing_tasks[repo_id]["total"] = stats["total_files"]
                        state.indexing_tasks[repo_id]["errors"] = stats["errors"]
                
                with state.lock:
                    state.indexing_tasks[repo_id]["status"] = "completed"
            except Exception as e:
                with state.lock:
                    state.indexing_tasks[repo_id]["status"] = "error"
                    state.indexing_tasks[repo_id]["error"] = str(e)
        
        state.executor.submit(index_task)
        
        return {
            "task_id": repo_id,
            "status": "started",
            "message": "Indexing started in background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        
        results = search_manager.search(query_embedding, top_k=request.top_k)
        
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
    
    :param request: Repository path request
    :returns: Detailed statistics about the repository
    """
    try:
        repo_manager = state.get_repo_manager(request.repo_path)
        index_manager = repo_manager.index_manager
        storage_manager = repo_manager.storage_manager
        search_manager = repo_manager.search_manager
        
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
        
        work_tree = repo_manager.repository.get_work_tree_root()
        
        eligible_files = []
        for file_path in work_tree.rglob("*"):
            if file_path.is_file() and ".filex" not in file_path.parts:
                eligible_files.append(str(file_path))
        
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
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/progress/{repo_id}")
async def get_progress(repo_id: str):
    """
    Get indexing progress for a repository.
    
    :param repo_id: Repository path (used as task ID)
    :returns: Current indexing progress
    """
    with state.lock:
        if repo_id not in state.indexing_tasks:
            return JSONResponse(
                status_code=404,
                content={"error": "No indexing task found for this repository"}
            )
        
        task_info = state.indexing_tasks[repo_id].copy()
    
    return task_info


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
