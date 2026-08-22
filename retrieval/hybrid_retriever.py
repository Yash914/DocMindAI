from retrieval.retriever import Retriever
from retrieval.graph_retriever import GraphRetriever


class HybridRetriever:

    def __init__(self, graph, vector_top_k=3, graph_top_k=3):

        self.vector_retriever = Retriever()

        self.graph_retriever = GraphRetriever(
            graph
        )

        self.vector_top_k = vector_top_k
        self.graph_top_k = graph_top_k

    # --------------------------------------------------------
    # HYBRID SEARCH
    # --------------------------------------------------------

    def search(self, query):

        # ----------------------------------------------------
        # Vector retrieval
        # ----------------------------------------------------

        vector_results = (
            self.vector_retriever.search(
                query,
                top_k=self.vector_top_k
            )
        )

        # ----------------------------------------------------
        # Graph retrieval
        # ----------------------------------------------------

        graph_results = (
            self.graph_retriever.search(
                query,
                top_k=self.graph_top_k
            )
        )

        # ----------------------------------------------------
        # Build unified context
        # ----------------------------------------------------

        context = []

        # Vector context
        for result in vector_results:

            chunk = result["document"]

            context.append(
                {
                    "type": "document",

                    "score": result["score"],

                    "chunk_id":
                        chunk.get(
                            "chunk_id",
                            ""
                        ),

                    "page":
                        chunk.get(
                            "page_number",
                            None
                        ),

                    "text":
                        chunk.get(
                            "text",
                            ""
                        )
                }
            )

        # Graph context
        for result in graph_results:

            context.append(
                {
                    "type": "graph",

                    "score":
                        result.get(
                            "score",
                            0
                        ),

                    "subject":
                        result.get(
                            "subject",
                            ""
                        ),

                    "predicate":
                        result.get(
                            "predicate",
                            ""
                        ),

                    "object":
                        result.get(
                            "object",
                            ""
                        ),

                    "evidence":
                        result.get(
                            "evidence",
                            ""
                        ),

                    "document":
                        result.get(
                            "document",
                            ""
                        ),

                    "page":
                        result.get(
                            "page",
                            None
                        ),

                    "chunk":
                        result.get(
                            "chunk",
                            ""
                        )
                }
            )

        return {
            "query": query,

            "vector_results":
                vector_results,

            "graph_results":
                graph_results,

            "context":
                context
        }