from pathlib import Path
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT
# ============================================================

from retrieval.retriever import Retriever


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PERSISTENT VECTOR RETRIEVAL TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD SAVED RETRIEVER
    # --------------------------------------------------------

    retriever = Retriever()

    # --------------------------------------------------------
    # QUESTIONS
    # --------------------------------------------------------

    questions = [

        "What standard must cement conform to?",

        "How is cement tested?",

        "What are the requirements for cement?",

        "What is the procedure for testing cement?"
    ]

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    for question in questions:

        print("\n" + "-" * 70)

        print(
            f"QUESTION: {question}"
        )

        print("-" * 70)

        results = retriever.search(
            question,
            top_k=3
        )

        for i, result in enumerate(
            results,
            start=1
        ):

            chunk = result["document"]

            score = result["score"]

            print(
                f"\n{i}. Score: {score:.4f}"
            )

            print(
                f"Chunk: {chunk['chunk_id']}"
            )

            print(
                f"Page: {chunk['page_number']}"
            )

            print(
                f"Source type: "
                f"{chunk['source_type']}"
            )

            print(
                "Text:"
            )

            print(
                chunk["text"][:500]
            )

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PERSISTENT RETRIEVAL TEST COMPLETE")
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()