"""Tests for embedding service."""

import pytest
from task_context_mcp.services import (
    generate_embedding,
    generate_embeddings,
    get_embedding_model,
    reset_model,
)
from task_context_mcp.config.settings import get_settings


def test_get_embedding_model(test_settings, mock_sentence_transformer):
    """Test getting embedding model."""
    model = get_embedding_model()
    assert model is not None
    
    # Should return same instance
    model2 = get_embedding_model()
    assert model is model2


def test_generate_embedding(test_settings, mock_sentence_transformer):
    """Test generating single embedding."""
    text = "This is a test document for embedding generation."
    embedding = generate_embedding(text)
    
    assert embedding is not None
    assert isinstance(embedding, list)
    
    settings = get_settings()
    assert len(embedding) == settings.embedding_dimension


def test_generate_embeddings_batch(test_settings, mock_sentence_transformer):
    """Test generating multiple embeddings."""
    texts = [
        "First test document",
        "Second test document",
        "Third test document",
    ]
    embeddings = generate_embeddings(texts)
    
    assert len(embeddings) == 3
    
    settings = get_settings()
    for embedding in embeddings:
        assert isinstance(embedding, list)
        assert len(embedding) == settings.embedding_dimension


def test_embedding_similarity(test_settings, mock_sentence_transformer):
    """Test that embeddings can be compared."""
    text1 = "The cat sits on the mat"
    text2 = "A cat is sitting on a mat"
    text3 = "The weather is sunny today"
    
    emb1 = generate_embedding(text1)
    emb2 = generate_embedding(text2)
    emb3 = generate_embedding(text3)
    
    # Calculate cosine similarity
    def cosine_similarity(a, b):
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(y * y for y in b) ** 0.5
        return dot_product / (magnitude_a * magnitude_b)
    
    sim_1_2 = cosine_similarity(emb1, emb2)
    sim_1_3 = cosine_similarity(emb1, emb3)
    
    # Just verify we can compute similarities (mock generates random embeddings)
    assert isinstance(sim_1_2, float)
    assert isinstance(sim_1_3, float)


def test_reset_model(test_settings, mock_sentence_transformer):
    """Test resetting embedding model."""
    model1 = get_embedding_model()
    reset_model()
    model2 = get_embedding_model()
    
    # Should create new instance after reset
    assert model1 is not model2
