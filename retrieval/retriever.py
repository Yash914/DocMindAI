from pathlib import Path
import pickle

from retrieval.embedding_model import EmbeddingModel
from retrieval.vector_store import VectorStore


# ============================================================
# INDEX PATH
# ============================================================

RETRIEVAL_DIR = Path(__file__).resolve().parent

INDEX_PATH = RETRIEVAL_DIR / "vector_index.pkl"


# ============================================================
# RETRIEVER
# ============================================================

class Retriever:

    def __init__(self, index_path=INDEX_PATH):

        self.index_path = Path(index_path)

        self.embedding_model = EmbeddingModel()

        self.vector_store = VectorStore()

        self.chunks = []

        self.load_index()

    # --------------------------------------------------------
    # LOAD SAVED INDEX
    # --------------------------------------------------------

    def load_index(self):

        if not self.index_path.exists():

            raise FileNotFoundError(
                f"Vector index not found: "
                f"{self.index_path}\n"
                f"Run:\n"
                f"python retrieval/index_builder.py"
            )

        print(
            f"Loading vector index:"
        )

        print(
            self.index_path
        )

        with open(
            self.index_path,
            "rb"
        ) as file:

            index_data = pickle.load(
                file
            )

        vectors = index_data[
            "vectors"
        ]

        chunks = index_data[
            "chunks"
        ]

        self.vector_store.add(
            vectors,
            chunks
        )

        self.chunks = chunks

        print(
            f"Loaded {len(chunks)} chunks."
        )

        print(
            f"Vector dimensions: "
            f"{vectors.shape[1]}"
        )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    def search(
        self,
        query,
        top_k=5
    ):

        query_vector = (
            self.embedding_model.encode_one(
                query
            )
        )

        return self.vector_store.search(
            query_vector,
            top_k
        )