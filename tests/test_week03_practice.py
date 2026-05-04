from exercises.week03_practice import search_memory_hits


class FakeCollection:
    def __init__(self):
        self.last_query = None

    def query(self, query_texts, n_results):
        self.last_query = {"query_texts": query_texts, "n_results": n_results}
        return {
            "ids": [["memory-1"]],
            "documents": [["카나메이트 UI에서는 채팅 답변과 tool trace를 함께 보여준다."]],
            "distances": [[0.12]],
        }


def test_week03_formats_chroma_hits():
    collection = FakeCollection()

    hits = search_memory_hits("UI에서는 무엇을 보여줘?", top_k=2, collection=collection)

    assert collection.last_query == {"query_texts": ["UI에서는 무엇을 보여줘?"], "n_results": 2}
    assert hits == [
        {
            "id": "memory-1",
            "content": "카나메이트 UI에서는 채팅 답변과 tool trace를 함께 보여준다.",
            "distance": 0.12,
        }
    ]

