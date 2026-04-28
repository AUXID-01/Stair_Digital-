"""
indexing/vector_store.py
Responsibility: Reusable wrapper for ChromaDB persistent storage at the collection level.
Inputs: Indices, metadata, and vectors.
Outputs: Persistence on disk.
Dependencies: chromadb, config.py, logs/logger.py
"""

import chromadb
from chromadb.config import Settings
from typing import List, Optional
from config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME
from logs.logger import get_logger

log = get_logger("indexing.vector_store")

class VectorStore:
    """
    Handles local disk persistence via chromadb.PersistentClient.
    """
    def __init__(self, persist_path: str = CHROMA_PERSIST_DIR, collection_name: str = CHROMA_COLLECTION_NAME):
        self.persist_path = persist_path
        self.collection_name = collection_name
        self.client: Optional[chromadb.ClientAPI] = None
        self.collection = None

    def initialize(self):
        """Initializes the persistent client and the collection."""
        try:
            log.info("vector_store_init_start", path=self.persist_path)
            self.client = chromadb.PersistentClient(path=self.persist_path)
            log.info("vector_store_init_complete")

            log.info("collection_get_or_create", collection=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            log.error("vector_store_failure", error=str(e), stage="init")
            raise e

    def add_chunks(self, ids: List[str], documents: List[str], embeddings: List[List[float]], metadatas: List[dict]):
        """
        Inserts pre-generated embeddings and metadata into Chroma.
        """
        if not self.collection:
            self.initialize()

        try:
            log.info("collection_add_start", count=len(ids))
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            log.info("collection_add_complete", count=len(ids))
        except Exception as e:
            log.error("vector_store_failure", error=str(e), stage="add")
            raise e

    def count(self) -> int:
        """Returns the total number of items in the collection."""
        if not self.collection:
            self.initialize()
        return self.collection.count()
