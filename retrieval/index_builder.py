from pathlib import Path
import sys
import pickle


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from config import INPUT_DIR

from document_processor import process_document

from chunker.chunker import create_chunks

from retrieval.embedding_model import EmbeddingModel


# ============================================================
# PATHS
# ============================================================

RETRIEVAL_DIR = Path(__file__).resolve().parent

INDEX_PATH = RETRIEVAL_DIR / "vector_index.pkl"


# ============================================================
# BUILD INDEX
# ============================================================

def build_index():

    print("=" * 70)
    print("BUILDING VECTOR INDEX")
    print("=" * 70)

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    pdf_path = INPUT_DIR / "S-2_sr.pdf"

    print(f"PDF: {pdf_path.name}")

    # --------------------------------------------------------
    # PROCESS DOCUMENT
    # --------------------------------------------------------

    document = process_document(
        pdf_path
    )

    pages = document["pages"]

    print(
        f"Pages: {len(pages)}"
    )

    # --------------------------------------------------------
    # CHUNK
    # --------------------------------------------------------

    chunks = create_chunks(
        pages,
        chunk_size=1000,
        overlap=150
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    # --------------------------------------------------------
    # EMBEDDINGS
    # --------------------------------------------------------

    embedding_model = EmbeddingModel()

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print(
        f"Creating embeddings for "
        f"{len(texts)} chunks..."
    )

    vectors = embedding_model.encode(
        texts
    )

    print(
        f"Embedding shape: {vectors.shape}"
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    index_data = {

        "document": pdf_path.name,

        "chunks": chunks,

        "vectors": vectors
    }

    with open(
        INDEX_PATH,
        "wb"
    ) as file:

        pickle.dump(
            index_data,
            file
        )

    print(
        f"\nVector index saved to:"
    )

    print(
        INDEX_PATH
    )

    print("\n" + "=" * 70)
    print("INDEX BUILD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":

    build_index()