"""Portable lazy-loading transformer inference with integrated gradients."""

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


class TransformerModel:
    def __init__(self, checkpoint, length=128):
        self.checkpoint = str(checkpoint)
        self.length = length
        self.model = None
        self.tokenizer = None

    def __getstate__(self):
        return dict(checkpoint=self.checkpoint, length=self.length, model=None, tokenizer=None)

    def load(self):
        if self.model is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.checkpoint, local_files_only=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.checkpoint, local_files_only=True
            ).eval()

    def predict_proba(self, texts):
        self.load()
        output = []
        texts = list(texts)
        with torch.no_grad():
            for start in range(0, len(texts), 8):
                encoded = self.tokenizer(
                    texts[start : start + 8], padding=True, truncation=True, max_length=self.length, return_tensors="pt"
                )
                output.append(self.model(**encoded).logits.sigmoid().numpy())
        return np.vstack(output)

    def explain(self, text, index, limit=12):
        self.load()
        encoded = self.tokenizer(text, truncation=True, max_length=self.length, return_tensors="pt")
        ids = encoded.pop("input_ids")
        embeddings = self.model.get_input_embeddings()(ids).detach()
        baseline = torch.zeros_like(embeddings)
        gradients = torch.zeros_like(embeddings)
        steps = 16
        for step, alpha in enumerate(torch.linspace(0, 1, steps + 1)):
            value = (baseline + alpha * (embeddings - baseline)).requires_grad_(True)
            output = self.model(inputs_embeds=value, **encoded).logits[0, index]
            gradient = torch.autograd.grad(output, value)[0]
            gradients += gradient * (0.5 if step in (0, steps) else 1.0)
        contributions = ((embeddings - baseline) * gradients / steps).sum(-1)[0].detach().numpy()
        tokens = self.tokenizer.convert_ids_to_tokens(ids[0])
        ranked = sorted(zip(tokens, contributions), key=lambda pair: abs(pair[1]), reverse=True)
        return [
            dict(feature=token, contribution=float(value), method="integrated_gradients_zero_embedding_baseline")
            for token, value in ranked[:limit]
        ]
