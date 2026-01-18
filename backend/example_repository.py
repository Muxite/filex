"""
Example usage of the Repository system.
"""
from embedding import (
    TextEmbeddingHandler,
    SentenceTransformerEmbedder,
    FixedSizeChunker,
)
from file_handlers import TextFileHandler
from file_processor import FileProcessorRouter
from repo_manager import RepositoryManager
from logger import configure_logging


def main():
    configure_logging(level="INFO")
    
    print("=== Creating/Initializing Repository ===")
    repo_manager = RepositoryManager(create=True)
    
    print(f"Repository location: {repo_manager.repository.repo_path}")
    print(f"Work tree root: {repo_manager.repository.get_work_tree_root()}")
    
    print("\n=== Setting up File Processor ===")
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    chunker = FixedSizeChunker(chunk_size=512, overlap=50)
    embedding_handler = TextEmbeddingHandler(embedder=embedder, chunker=chunker)
    
    text_handler = TextFileHandler(embedding_handler=embedding_handler)
    processor = FileProcessorRouter(text_handler=text_handler)
    
    repo_manager.set_processor(processor)
    
    print("\n=== Indexing a Single File ===")
    try:
        result = repo_manager.index_file("README.md", force=True)
        print(f"Indexed: {result.get('indexed')}")
        print(f"Processed: {result.get('processed')}")
        if result.get('num_chunks'):
            print(f"Chunks: {result.get('num_chunks')}")
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    
    print("\n=== Getting Index Status ===")
    status = repo_manager.get_index_status()
    print(f"Total indexed files: {status['total_indexed_files']}")
    print(f"Text files: {status['text_files']}")
    print(f"Non-text files: {status['non_text_files']}")
    print(f"Total chunks: {status['total_chunks']}")
    print(f"Storage size: {status['storage_size']['total_bytes'] / 1024:.2f} KB")
    
    print("\n=== Listing Indexed Files ===")
    indexed_files = repo_manager.list_indexed_files()
    for file_info in indexed_files[:5]:
        print(f"- {file_info['file_path']} ({file_info['extension']})")
    
    print("\n=== Indexing Directory ===")
    try:
        stats = repo_manager.index_directory(
            recursive=True,
            extensions=['.txt', '.md', '.py'],
            force=False
        )
        print(f"Total files: {stats['total_files']}")
        print(f"Indexed: {stats['indexed']}")
        print(f"Skipped: {stats['skipped']}")
        print(f"Errors: {stats['errors']}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
