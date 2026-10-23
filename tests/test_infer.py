from app.ml import infer


def test_missing_model_never_fabricates_prediction(monkeypatch):
    monkeypatch.setattr(infer, "model_status", lambda: {"ready": False, "message": "missing"})
    result = infer.analyze_text("My friend is Muslim.", include_xai=False)
    assert result["classification"] == "UNCERTAIN"
    assert result["confidence"] == 0
    assert result["active_categories"] == []


def test_adapter_preserves_model_probability(monkeypatch):
    from src.utils.common import LABELS

    class Fake:
        def predict(self, texts, explain=False):
            return [
                dict(
                    binary_prediction="SAFE",
                    harmful_probability=0.12,
                    processed_text=texts[0],
                    labels=["SAFE"],
                    category_binary_disagreement=False,
                    notice="human review",
                    categories={label: dict(probability=0.03, threshold=0.4) for label in LABELS},
                )
            ]

    monkeypatch.setattr(infer, "model_status", lambda: {"ready": True})
    monkeypatch.setattr(infer, "_research_predictor", lambda: Fake())
    for text in ["My friend is Muslim.", "I hate this terrible idea.", "No hate, good work"]:
        result = infer.analyze_text(text, include_xai=False)
        assert result["harmful_probability"] == 0.12
        assert result["confidence"] == 0.88
        assert result["classification"] == "SAFE"
