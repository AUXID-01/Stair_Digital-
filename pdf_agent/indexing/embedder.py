"""
indexing/embedder.py
Responsibility: Reusable wrapper for generating high-quality embeddings using sentence-transformers.
Inputs: List of strings (chunks)
Outputs: List of vectors (embeddings)
Dependencies: sentence-transformers, config.py, logs/logger.py
"""

from typing import List
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL
from logs.logger import get_logger

log = get_logger("indexing.embedder")

class Embedder:
    """
    Sentence-transformer based embedding generator.
    Loads the model lazily on first use or upon instantiation.
    """
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """Lazily load the embedding model."""
        if self._model is None:
            try:
                log.info("embedding_model_load_start", model_name=self.model_name)
                self._model = SentenceTransformer(self.model_name)
                log.info("embedding_model_load_complete", model_name=self.model_name)
            except Exception as e:
                log.error("embedding_failure", error=str(e), stage="model_load")
                raise RuntimeError(f"Failed to load embedding model: {e}")

    def embed_text(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a batch of input texts.
        Returns a list of vectors (Python lists).
        """
        if not texts:
            log.warning("embedding_batch_empty", count=0)
            return []

        # Validate entries
        texts = [str(t) for t in texts if t and str(t).strip()]
        if not texts:
            log.error("embedding_failure", error="All input texts were empty/invalid", stage="input_validation")
            return []

        self._load_model()
        
        try:
            log.info("embedding_batch_start", batch_size=len(texts))
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            log.info("embedding_batch_complete", batch_size=len(texts))
            
            # Convert numpy arrays to lists for Chroma compatibility
            return embeddings.tolist()
        except Exception as e:
            log.error("embedding_failure", error=str(e), stage="generation")
            raise e
