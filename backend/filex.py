"""
FileX CLI entrypoint for indexing and searching files.
"""
import argparse
import sys
from pathlib import Path
from typing import Tuple

from src import (
    RepositoryManager,
    FileProcessorRouter,
    TextFileHandler,
    ImageFileHandler,
    TextEmbeddingHandler,
    SentenceTransformerEmbedder,
    CLIPImageEmbedder,
    FixedSizeChunker,
    SearchManager,
)


def parse_search_query(query_string: str) -> Tuple[str, int]:
    """
    Parse search query string with optional count flag.
    
    Supports formats like:
    - "types of fruits" (default count: 10)
    - "types of fruits -count 5"
    - "types of fruits --count 5"
    - "types of fruits -count --5"
    
    :param query_string: Query string with optional flags
    :returns: Tuple of (query_text, count)
    """
    query_parts = query_string.split()
    query_text_parts = []
    count = 10
    
    i = 0
    while i < len(query_parts):
        part = query_parts[i]
        
        if part in ("-count", "--count", "-c", "--c"):
            if i + 1 < len(query_parts):
                try:
                    count = int(query_parts[i + 1])
                    i += 2
                    continue
                except ValueError:
                    pass
        elif part.startswith("--") and part[2:].lstrip("-").isdigit():
            count = int(part[2:].lstrip("-"))
            i += 1
            continue
        
        query_text_parts.append(part)
        i += 1
    
    query_text = " ".join(query_text_parts)
    return query_text, count


def setup_components(
    model_name: str = "all-mpnet-base-v2",
    image_model_name: str = "openai/clip-vit-base-patch32"
) -> Tuple[RepositoryManager, TextEmbeddingHandler]:
    """
    Set up FileX components with default configuration.
    
    Note: Model loading can take 5-10 seconds on first run or when loading from cache.
    Subsequent runs are faster due to model caching.
    
    :param model_name: Sentence-transformer model name (default: all-mpnet-base-v2, 768 dimensions)
    :param image_model_name: CLIP model name for images (default: openai/clip-vit-base-patch32, 512 dimensions)
    :returns: Tuple of (RepositoryManager, TextEmbeddingHandler)
    """
    print("Loading embedding models (this may take a few seconds)...")
    embedder = SentenceTransformerEmbedder(model_name=model_name)
    chunker = FixedSizeChunker(chunk_size=512, overlap=50)
    embedding_handler = TextEmbeddingHandler(embedder=embedder, chunker=chunker)
    
    text_handler = TextFileHandler(embedding_handler=embedding_handler)
    
    try:
        image_embedder = CLIPImageEmbedder(model_name=image_model_name)
        image_handler = ImageFileHandler(image_embedder=image_embedder)
        processor = FileProcessorRouter(text_handler=text_handler, image_handler=image_handler)
    except Exception as e:
        print(f"Warning: Could not initialize image handler: {e}")
        print("Image support will be disabled. Text files will still work.")
        processor = FileProcessorRouter(text_handler=text_handler)
    
    repo_manager = RepositoryManager(processor=processor, create=True)
    
    return repo_manager, embedding_handler


def cmd_index(args: argparse.Namespace) -> int:
    """
    Handle index command.
    
    :param args: Parsed command-line arguments
    :returns: Exit code (0 for success, non-zero for error)
    """
    try:
        print("Initializing FileX...")
        model_name = args.model if hasattr(args, 'model') and args.model else "all-mpnet-base-v2"
        repo_manager, _ = setup_components(model_name=model_name)
        
        if args.path:
            if Path(args.path).is_file():
                print(f"Indexing file: {args.path}")
                result = repo_manager.index_file(args.path, force=args.force)
                if result.get("indexed"):
                    print(f"✓ Indexed: {result['file_path']}")
                    if result.get("processed"):
                        print(f"  Chunks: {result.get('num_chunks', 0)}")
                else:
                    print(f"- Skipped: {result.get('reason', 'Unknown reason')}")
            else:
                print(f"Indexing directory: {args.path}")
                stats = repo_manager.index_directory(
                    directory=args.path,
                    recursive=not args.no_recursive,
                    extensions=args.extensions,
                    force=args.force,
                )
                print(f"\nIndexing complete:")
                print(f"  Total files: {stats['total_files']}")
                print(f"  Indexed: {stats['indexed']}")
                print(f"  Skipped: {stats['skipped']}")
                if stats['errors'] > 0:
                    print(f"  Errors: {stats['errors']}")
                    for error in stats['error_messages']:
                        print(f"    - {error}")
        else:
            print("Indexing all files in repository...")
            stats = repo_manager.index_directory(
                recursive=not args.no_recursive,
                extensions=args.extensions,
                force=args.force,
            )
            print(f"\nIndexing complete:")
            print(f"  Total files: {stats['total_files']}")
            print(f"  Indexed: {stats['indexed']}")
            print(f"  Skipped: {stats['skipped']}")
            if stats['errors'] > 0:
                print(f"  Errors: {stats['errors']}")
                for error in stats['error_messages']:
                    print(f"    - {error}")
        
        return 0
    except Exception as e:
        print(f"Error during indexing: {e}", file=sys.stderr)
        return 1


def cmd_search(args: argparse.Namespace) -> int:
    """
    Handle search command.
    
    :param args: Parsed command-line arguments
    :returns: Exit code (0 for success, non-zero for error)
    """
    try:
        print("Initializing FileX...")
        model_name = args.model if hasattr(args, 'model') and args.model else "all-mpnet-base-v2"
        repo_manager, embedding_handler = setup_components(model_name=model_name)
        search_manager = repo_manager.search_manager
        
        query_text, count = parse_search_query(args.query)
        
        if args.count:
            count = args.count
        
        print(f"Searching for: '{query_text}' (top {count} results)")
        
        _, query_embedding = embedding_handler.embed_text(query_text)
        if query_embedding.ndim > 1 and query_embedding.shape[0] == 1:
            query_embedding = query_embedding[0]
        
        results = search_manager.search(query_embedding, top_k=count)
        
        if not results:
            print("No results found.")
            return 0
        
        print(f"\nFound {len(results)} result(s):\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.file_name} (similarity: {result.similarity_score:.4f})")
            print(f"   Path: {result.file_path}")
            print(f"   Chunk {result.chunk_index}: {result.chunk_text[:200]}...")
            print()
        
        return 0
    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """
    Handle status command.
    
    Does not load the embedding model for faster execution.
    
    :param args: Parsed command-line arguments
    :returns: Exit code (0 for success, non-zero for error)
    """
    try:
        from src import Repository, IndexManager, StorageManager, SearchManager
        
        repository = Repository(create=False)
        index_manager = IndexManager(repository)
        storage_manager = StorageManager(repository)
        search_manager = SearchManager(repository)
        
        index_status = {
            "total_indexed_files": index_manager.get_indexed_files_count(),
            "text_files": sum(1 for e in index_manager.get_all_entries() if e.is_text_type),
            "non_text_files": sum(1 for e in index_manager.get_all_entries() if not e.is_text_type),
            "total_chunks": sum(e.num_chunks or 0 for e in index_manager.get_all_entries() if e.is_text_type),
            "storage_size": storage_manager.get_storage_size(),
            "repository_path": str(repository.repo_path),
            "work_tree_root": str(repository.get_work_tree_root()),
        }
        search_stats = search_manager.get_index_stats()
        
        print("FileX Repository Status")
        print("=" * 50)
        print(f"Repository: {index_status['repository_path']}")
        print(f"Work tree: {index_status['work_tree_root']}")
        print()
        print("Index Statistics:")
        print(f"  Total indexed files: {index_status['total_indexed_files']}")
        print(f"  Text files: {index_status['text_files']}")
        print(f"  Non-text files: {index_status['non_text_files']}")
        print(f"  Total chunks: {index_status['total_chunks']}")
        print()
        print("Search Index Statistics:")
        print(f"  Total chunks: {search_stats['total_chunks']}")
        print(f"  Unique files: {search_stats['unique_files']}")
        print(f"  Embedding dimension: {search_stats['embedding_dimension']}")
        print()
        storage = index_status['storage_size']
        print("Storage:")
        print(f"  Embeddings: {storage['embeddings_bytes'] / (1024*1024):.2f} MB")
        print(f"  Metadata: {storage['metadata_bytes'] / 1024:.2f} KB")
        print(f"  Total: {storage['total_bytes'] / (1024*1024):.2f} MB")
        
        return 0
    except Exception as e:
        print(f"Error getting status: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """
    Main entry point for FileX CLI.
    
    :returns: Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="FileX - Semantic file indexing and search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    index_parser = subparsers.add_parser("index", help="Index files for search")
    index_parser.add_argument(
        "path",
        nargs="?",
        help="File or directory to index (default: all files in repository)",
    )
    index_parser.add_argument(
        "--force",
        action="store_true",
        help="Force reindexing even if files haven't changed",
    )
    index_parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't recursively index subdirectories",
    )
    index_parser.add_argument(
        "--extensions",
        nargs="+",
        help="Only index files with these extensions (e.g., --extensions .txt .docx)",
    )
    index_parser.add_argument(
        "--model",
        type=str,
        default="all-mpnet-base-v2",
        help="Embedding model to use (default: all-mpnet-base-v2, 768 dimensions)",
    )
    
    search_parser = subparsers.add_parser("search", help="Search indexed files")
    search_parser.add_argument(
        "query",
        help="Search query (e.g., 'types of fruits -count 5' or 'types of fruits --3')",
    )
    search_parser.add_argument(
        "--count",
        "-c",
        type=int,
        help="Number of results to return (overrides query flags)",
    )
    search_parser.add_argument(
        "--model",
        type=str,
        default="all-mpnet-base-v2",
        help="Embedding model to use (default: all-mpnet-base-v2, 768 dimensions)",
    )
    
    status_parser = subparsers.add_parser("status", help="Show repository status")
    status_parser.add_argument(
        "--model",
        type=str,
        default="all-mpnet-base-v2",
        help="Embedding model to use (default: all-mpnet-base-v2, 768 dimensions)",
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "index":
        return cmd_index(args)
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "status":
        return cmd_status(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
