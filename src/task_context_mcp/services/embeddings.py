"""Embedding service for generating semantic embeddings."""

from sentence_transformers import SentenceTransformer
from loguru import logger

from ..config.settings import get_settings

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """Get or create the sentence transformer model singleton.
    
    Returns:
        Sentence transformer model instance
    """
    global _model
    
    if _model is None:
        settings = get_settings()
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        logger.info(f"Embedding model loaded with dimension: {settings.embedding_dimension}")
    
    return _model


def generate_embedding(text: str) -> list[float]:
    """Generate embedding for a single text.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector as list of floats
    """
    model = get_embedding_model()
    embedding = model.encode([text], convert_to_numpy=True)
    # Extract first embedding from batch result
    return embedding[0].tolist()


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts (batch processing).
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()


def reset_model() -> None:
    """Reset the model singleton (mainly for testing)."""
    global _model
    _model = None
    logger.info("Embedding model reset")
