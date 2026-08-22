import numpy as np


class VectorStore:

    def __init__(self):

        self.vectors = []
        self.documents = []

    def add(
        self,
        vectors,
        documents
    ):

        vectors = np.asarray(
            vectors
        )

        if len(vectors) != len(documents):

            raise ValueError(
                "Number of vectors and documents "
                "must be the same."
            )

        self.vectors.extend(
            vectors
        )

        self.documents.extend(
            documents
        )

    def search(
        self,
        query_vector,
        top_k=5
    ):

        if not self.vectors:

            return []

        matrix = np.asarray(
            self.vectors
        )

        query_vector = np.asarray(
            query_vector
        )

        # Because embeddings are normalized,
        # dot product = cosine similarity.
        scores = matrix @ query_vector

        indices = np.argsort(
            scores
        )[::-1][:top_k]

        results = []

        for index in indices:

            results.append(
                {
                    "score": float(
                        scores[index]
                    ),
                    "document":
                        self.documents[index]
                }
            )

        return results