import json
import numpy as np
import pandas as pd
import pytest
torch = pytest.importorskip("torch")
import yaml
from fastapi.testclient import TestClient
from src.utils.common import ROOT, LABELS
from src.preprocessing.text import preprocess, language_metadata
from src.preprocessing.roman_urdu import normalize_roman_urdu
from src.data.prepare import map_label, deduplicate, split_data
from src.evaluation.metrics import optimize_thresholds, evaluate
from src.models.baseline import Baseline
from src.training.train_transformer import masked_loss
from src.inference.predict import Predictor


def test_english_ambiguity_and_spacing():
    assert normalize_roman_urdu("he told me or the main men") == "he told me or the main men"
    assert normalize_roman_urdu("tm nhi, bohot acha!") == "tum nahi, bohat acha!"


def test_urdu_unicode_emoji_and_html():
    assert preprocess("<b>كي</b> 😀 https://example.com @person") == "کی 😀 urltoken usertoken"
    assert preprocess(None) == ""
    assert preprocess("   ") == ""


def test_language():
    assert language_metadata("آپ کیسے ہیں")["script"] == "arabic"
    assert language_metadata("you are nice")["language"] == "English"
    assert language_metadata("tum bohat acha")["language"] == "Roman_Urdu"
    assert language_metadata("you آپ")["code_mixed"]


def test_partial_mapping():
    mapping = yaml.safe_load((ROOT / "configs/label_mapping.yaml").read_text())
    y = map_label("roman_urdu_toxic", 1, mapping)
    assert y[LABELS.index("TOXIC")] == 1
    assert y[LABELS.index("THREAT")] == -1
    assert y[LABELS.index("CYBERBULLYING")] == -1
    with pytest.raises(ValueError):
        map_label("roman_urdu_toxic", "ambiguous", mapping)


def test_duplicate_conflict_quarantine():
    rows = []
    for text, value in [("same text", 1), ("same text", 0), ("a completely distinct sentence", 0)]:
        rows.append(dict(processed_text=text, **{label: value for label in LABELS}))
    result, audit = deduplicate(pd.DataFrame(rows))
    assert len(result) == 1 and audit["conflicting_exact_rows"] == 2


def test_near_duplicate():
    text = "This is a fairly long sentence with many repeated words for duplicate checking"
    frame = pd.DataFrame([dict(processed_text=s, **{label: 0 for label in LABELS}) for s in [text, text + "!"]])
    assert len(deduplicate(frame)[0]) == 1


def test_iterative_splits_reproducible():
    rng = np.random.default_rng(42)
    frame = pd.DataFrame(rng.integers(0, 2, (100, 8)), columns=LABELS)
    a, b = split_data(frame), split_data(frame)
    assert a.equals(b)
    # Iterative stratification prioritizes marginal labels and can vary small-set sizes.
    counts = a.split.value_counts().to_dict()
    assert sum(counts.values()) == 100
    assert abs(counts["train"] - 70) <= 3
    assert abs(counts["validation"] - 15) <= 3
    assert abs(counts["test"] - 15) <= 3


def test_unknown_cells_do_not_change_scores():
    y = np.full((4, 8), -1)
    y[:, 0] = [0, 1, 0, 1]
    p = np.zeros((4, 8))
    p[:, 0] = [0.1, 0.9, 0.1, 0.9]
    m = evaluate(y, p, np.full(8, 0.5))
    p[:, 1:] = 1
    assert evaluate(y, p, np.full(8, 0.5))["macro_f1"] == m["macro_f1"] == 1


def test_thresholds_and_disabled_class():
    y = np.array([[0, 0], [1, 0], [1, 0]])
    p = np.array([[0.1, 0.2], [0.3, 0.2], [0.4, 0.2]])
    t = optimize_thresholds(y, p)
    assert 0.1 < t[0] <= 0.3 and t[1] > 1


def test_sparse_model_partial_heads():
    x = ["nice sunny day", "good kind friend", "rude mean comment", "bad angry reply"] * 3
    y = np.array([[0, -1], [0, -1], [1, -1], [1, -1]] * 3)
    model = Baseline(min_df=1).fit(x, y)
    scores = model.predict_proba(["nice friend"])
    assert scores.shape == (1, 2) and scores[0, 1] == 0


def test_masked_loss_zero_unknown_gradient():
    logits = torch.zeros((2, 2), requires_grad=True)
    loss = masked_loss(logits, torch.tensor([[1.0, -1.0], [0.0, -1.0]]), torch.ones(2))
    loss.backward()
    assert torch.all(logits.grad[:, 1] == 0)


def test_tiny_transformer_training_smoke():
    # Random tiny architecture validates the optimization path, not pretrained research performance.
    from transformers import BertConfig, BertForSequenceClassification

    model = BertForSequenceClassification(
        BertConfig(
            vocab_size=20,
            hidden_size=16,
            num_hidden_layers=1,
            num_attention_heads=2,
            intermediate_size=32,
            num_labels=9,
        )
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
    logits = model(input_ids=torch.tensor([[1, 2, 3], [3, 2, 1]]), attention_mask=torch.ones((2, 3))).logits
    labels = torch.zeros((2, 9))
    labels[0, -1] = 1
    labels[:, 0] = -1
    loss = masked_loss(logits, labels, torch.ones(9), focal=True)
    loss.backward()
    optimizer.step()
    assert torch.isfinite(loss)


def test_corrupt_artifact(tmp_path):
    (tmp_path / "broken.joblib").write_bytes(b"broken")
    (tmp_path / "selected.json").write_text(json.dumps(dict(path="broken.joblib", sha256="wrong")))
    with pytest.raises(ValueError):
        Predictor(tmp_path)


def test_api_missing_model(monkeypatch):
    from app.api import research_v2
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(research_v2.router)

    def unavailable():
        raise FileNotFoundError()

    monkeypatch.setattr(research_v2, "predictor", unavailable)
    client = TestClient(app)
    assert client.post("/predict", json={"text": "hello"}).status_code == 503
    assert client.get("/labels").status_code == 200
    assert client.post("/predict", json={"text": ""}).status_code == 422
