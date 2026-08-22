from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingModel:

    def __init__(self):

        print(
            f"Loading embedding model: {MODEL_NAME}"
        )

        self.model = SentenceTransformer(
            MODEL_NAME
        )

        print("Embedding model loaded.")

    def encode(self, texts):

        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

    def encode_one(self, text):

        return self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )