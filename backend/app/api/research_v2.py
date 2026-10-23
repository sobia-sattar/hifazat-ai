"""Research endpoints return unmodified fitted probabilities and frozen decisions."""

import csv
from functools import lru_cache
import io
import json
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field
from src.inference.predict import Predictor
from src.utils.common import LABELS, ROOT

router = APIRouter()


@router.get('/paper')
def paper():
    path = ROOT / 'output/pdf/BullyLens_X_Research_Paper.pdf'
    if not path.exists():
        raise HTTPException(404, 'Research paper has not been built.')
    return FileResponse(path, media_type='application/pdf', filename=path.name)


@router.get("/results")
def results():
    path = ROOT / "reports/final_metrics.json"
    if not path.exists():
        raise HTTPException(404, "No completed evaluation")
    return json.loads(path.read_text())


@lru_cache(maxsize=1)
def predictor():
    return Predictor()


def ready():
    try:
        return predictor()
    except Exception as exc:
        raise HTTPException(503, "Research model unavailable or invalid; train and verify artifacts.") from exc


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


@router.get("/health")
def health():
    try:
        ready()
        return {"status": "ready"}
    except HTTPException:
        return {"status": "unavailable"}


@router.get("/labels")
def labels():
    return {"labels": ["SAFE"] + LABELS, "safe_definition": "No harmful category exceeds its frozen threshold."}


@router.get("/model/info")
def info():
    return {k: v for k, v in ready().bundle.items() if k != "model"}


@router.post("/predict")
def predict(body: TextRequest):
    try:
        return ready().predict([body.text], explain=True)[0]
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/predict/batch")
def batch(file: UploadFile = File(...)):
    content = file.file.read(2_000_001)
    if len(content) > 2_000_000:
        raise HTTPException(413, "CSV limit is 2 MB")
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
        if not reader.fieldnames or "text" not in reader.fieldnames:
            raise ValueError("CSV needs a text column")
        texts = []
        for row in reader:
            texts.append(row["text"])
            if len(texts) > 1000:
                raise ValueError("CSV limit is 1000 rows")
        predictions = ready().predict(texts)
    except (UnicodeError, ValueError, csv.Error) as exc:
        raise HTTPException(422, str(exc)) from exc
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["text", "language", "harmful_probability", "binary_prediction"]
        + [label.lower() + "_probability" for label in LABELS],
    )
    writer.writeheader()
    for row in predictions:
        # Prevent spreadsheet formula execution on exported user-controlled text.
        text = row["text"]
        if text.lstrip().startswith(("=", "+", "-", "@")):
            text = "'" + text
        writer.writerow(
            dict(
                text=text,
                language=row["language"],
                harmful_probability=row["harmful_probability"],
                binary_prediction=row["binary_prediction"],
                **{label.lower() + "_probability": row["categories"][label]["probability"] for label in LABELS},
            )
        )
    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=predictions.csv"},
    )
