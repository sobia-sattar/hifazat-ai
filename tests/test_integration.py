"""Integration checks use actual local artifacts without asserting subjective labels."""

import csv
import io
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.research_v2 import router
from src.inference.predict import Predictor
from src.utils.common import LABELS


def test_saved_model_languages_and_thresholds():
    model = Predictor()
    for row in model.predict(["You are welcome.", "آپ کیسے ہیں", "tum bohat acha", "you آپ"]):
        assert 0 <= row["harmful_probability"] <= 1
        assert row["binary_prediction"] == (
            "HARMFUL" if row["harmful_probability"] >= row["binary_threshold"] else "SAFE"
        )
        expected = [
            label
            for label in LABELS
            if row["categories"][label]["probability"] >= row["categories"][label]["threshold"]
        ]
        assert row["labels"] == (expected or ["SAFE"])


def test_api_success_and_csv():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ready"
    assert client.get("/model/info").status_code == 200
    response = client.post("/predict", json={"text": "Thank you for your help."})
    assert response.status_code == 200
    result = client.post("/predict/batch", files={"file": ("input.csv", b"text\nhello friend\n=SUM(1)\n", "text/csv")})
    assert result.status_code == 200
    records = list(csv.DictReader(io.StringIO(result.text)))
    assert len(records) == 2
    assert records[1]["text"].startswith("'")
    assert "toxic_probability" in records[0]
    assert client.post("/predict/batch", files={"file": ("x.csv", b"wrong\nhello\n", "text/csv")}).status_code == 422
    assert client.post("/predict", json={"text": "   "}).status_code == 422
