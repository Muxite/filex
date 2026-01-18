"""
Example showing how to configure and use logging.
"""
from file_processor import FileProcessorRouter
from file_handlers import TextFileHandler
from embedding import (
    TextEmbeddingHandler,
    SentenceTransformerEmbedder,
    FixedSizeChunker,
)
from logger import configure_logging

def main():
    configure_logging(level="INFO")
    
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    chunker = FixedSizeChunker(chunk_size=512, overlap=50)
    embedding_handler = TextEmbeddingHandler(embedder=embedder, chunker=chunker)
    
    text_handler = TextFileHandler(embedding_handler=embedding_handler)
    router = FileProcessorRouter(text_handler=text_handler)
    
    print("\n=== Processing with INFO level logging ===")
    try:
        result = router.process_file("sample.txt")
        print(f"Processed: {result['processed']}")
    except FileNotFoundError:
        print("Sample file not found (this is expected in this example)")
    
    print("\n=== Processing with DEBUG level logging ===")
    configure_logging(level="DEBUG")
    embedder2 = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    embedding_handler2 = TextEmbeddingHandler(embedder=embedder2, chunker=chunker)
    text_handler2 = TextFileHandler(embedding_handler=embedding_handler2)
    router2 = FileProcessorRouter(text_handler=text_handler2)
    
    try:
        result = router2.process_file("sample.txt")
        print(f"Processed: {result['processed']}")
    except FileNotFoundError:
        print("Sample file not found (this is expected in this example)")


if __name__ == "__main__":
    main()
