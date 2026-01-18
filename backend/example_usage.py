"""
Example usage of the TextEmbeddingHandler.
"""
from embedding import (
    TextEmbeddingHandler,
    SentenceTransformerEmbedder,
    FixedSizeChunker,
    SentenceAwareChunker,
)


def main():
    embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    
    fixed_chunker = FixedSizeChunker(chunk_size=512, overlap=50)
    handler_fixed = TextEmbeddingHandler(embedder=embedder, chunker=fixed_chunker)
    
    sentence_chunker = SentenceAwareChunker(target_chunk_size=500, max_chunk_size=1000)
    handler_sentence = TextEmbeddingHandler(embedder=embedder, chunker=sentence_chunker)
    
    sample_text = "This is a sample document. " * 100
    
    chunks, embeddings = handler_fixed.embed_text(sample_text)
    print(f"Fixed chunker produced {len(chunks)} chunks")
    print(f"Embeddings shape: {embeddings.shape}")
    
    chunks2, embeddings2 = handler_sentence.embed_text(sample_text)
    print(f"Sentence-aware chunker produced {len(chunks2)} chunks")
    print(f"Embeddings shape: {embeddings2.shape}")
    
    larger_text = sample_text * 10
    estimate = handler_fixed.get_estimated_chunk_count(larger_text)
    print(f"Estimated chunks for larger document: {estimate}")


if __name__ == "__main__":
    main()
