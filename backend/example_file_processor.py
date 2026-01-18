"""
Example usage of the FileProcessorRouter.
"""
from file_processor import FileProcessorRouter
from file_handlers import TextFileHandler
from embedding import (
    TextEmbeddingHandler,
    SentenceTransformerEmbedder,
    FixedSizeChunker,
)


def main():
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    chunker = FixedSizeChunker(chunk_size=512, overlap=50)
    embedding_handler = TextEmbeddingHandler(embedder=embedder, chunker=chunker)
    
    text_handler = TextFileHandler(embedding_handler=embedding_handler)
    
    router = FileProcessorRouter(text_handler=text_handler)
    
    text_file_path = "sample.txt"
    docx_file_path = "sample.docx"
    unsupported_file_path = "sample.py"
    
    print("Processing text file:")
    result = router.process_file(text_file_path)
    print(f"Processed: {result['processed']}")
    print(f"File size: {result['metadata']['file_size_bytes']} bytes")
    if result['embeddings']:
        print(f"Number of chunks: {result['embeddings']['num_chunks']}")
        print(f"Embedding dimension: {result['embeddings']['embedding_dimension']}")
    
    print("\nProcessing DOCX file:")
    result = router.process_file(docx_file_path)
    print(f"Processed: {result['processed']}")
    print(f"File size: {result['metadata']['file_size_kb']:.2f} KB")
    
    print("\nProcessing unsupported file:")
    result = router.process_file(unsupported_file_path)
    print(f"Processed: {result['processed']}")
    print(f"File size: {result['metadata']['file_size_bytes']} bytes")
    print(f"Reason: {result['reason']}")
    
    print("\nGetting metadata only:")
    metadata = router.get_file_metadata(text_file_path)
    print(f"File: {metadata.file_name}")
    print(f"Type: {metadata.file_extension}")
    print(f"Size: {metadata.file_size_mb:.2f} MB")
    print(f"Is text type: {metadata.is_text_type}")


if __name__ == "__main__":
    main()
