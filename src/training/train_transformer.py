"""Resource-aware Hugging Face training with masked BCE/focal loss and resumable epochs."""

import argparse
import random
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from src.evaluation.metrics import evaluate, optimize_thresholds
from src.utils.common import ROOT, LABELS, digest, write_json


def masked_loss(logits, labels, pos_weight, focal=False):
    known = labels >= 0
    target = labels.clamp(min=0)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, target, pos_weight=pos_weight, reduction="none")
    if focal:
        pt = torch.where(target.bool(), logits.sigmoid(), 1 - logits.sigmoid())
        loss = loss * (1 - pt).pow(2)
    return (loss * known).sum() / known.sum().clamp(min=1)


class TextDataset(Dataset):
    def __init__(self, frame, tokenizer, length):
        self.texts = frame.processed_text.tolist()
        self.y = np.c_[frame[LABELS].values, frame.binary_harmful.values].astype("float32")
        self.tokenizer, self.length = tokenizer, length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, i):
        item = self.tokenizer(
            self.texts[i], truncation=True, padding="max_length", max_length=self.length, return_tensors="pt"
        )
        return {**{k: v.squeeze(0) for k, v in item.items()}, "labels": torch.tensor(self.y[i])}


def main(args):
    if not torch.cuda.is_available() and not args.allow_cpu:
        print("NOT TRAINED: CPU-only host. Use --allow-cpu explicitly for an expensive CPU run.")
        return
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.use_deterministic_algorithms(True, warn_only=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data = ROOT / "data/processed/research.csv"
    frame = pd.read_csv(data)
    train, val = frame[frame.split == "train"], frame[frame.split == "validation"]
    folder = ROOT / "artifacts/transformers" / f"{args.model}-{args.length}"
    folder.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=len(LABELS) + 1, problem_type="multi_label_classification"
    ).to(device)
    tr = DataLoader(TextDataset(train, tokenizer, args.length), batch_size=args.batch_size, shuffle=True)
    va = DataLoader(TextDataset(val, tokenizer, args.length), batch_size=args.batch_size)
    labels = torch.tensor(tr.dataset.y)
    positive = (labels == 1).sum(0)
    negative = (labels == 0).sum(0)
    weights = (negative / positive.clamp(min=1)).clamp(min=1, max=100).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    total = ((len(tr) + args.accumulation - 1) // args.accumulation) * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.1 * total), total)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    start, best, stale, history = 0, -1.0, 0, []
    checkpoint = folder / "resume.pt"
    if args.resume and checkpoint.exists():
        state = torch.load(checkpoint, map_location=device, weights_only=False)
        if state["dataset_version"] != digest(data) or state["arguments"] != {
            k: v for k, v in vars(args).items() if k != "resume"
        }:
            raise ValueError("Resume dataset or arguments changed")
        model.load_state_dict(state["model"])
        optimizer.load_state_dict(state["optimizer"])
        scheduler.load_state_dict(state["scheduler"])
        scaler.load_state_dict(state["scaler"])
        start, best, stale, history = state["epoch"] + 1, state["best"], state["stale"], state["history"]
        torch.set_rng_state(state["rng"].cpu())
        if device.type == "cuda":
            torch.cuda.set_rng_state_all(state["cuda_rng"])
    for epoch in range(start, args.epochs):
        model.train()
        optimizer.zero_grad()
        losses = []
        for step, batch in enumerate(tr):
            target = batch.pop("labels").to(device)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = model(**{k: v.to(device) for k, v in batch.items()}).logits
                loss = masked_loss(logits, target, weights, args.focal)
            group_start = (step // args.accumulation) * args.accumulation
            group_size = min(args.accumulation, len(tr) - group_start)
            scaler.scale(loss / group_size).backward()
            losses.append(float(loss.detach().cpu()))
            if (step + 1) % args.accumulation == 0 or step + 1 == len(tr):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()
        model.eval()
        probabilities = []
        with torch.no_grad():
            for batch in va:
                batch.pop("labels")
                probabilities.append(
                    model(**{k: v.to(device) for k, v in batch.items()}).logits.sigmoid().cpu().numpy()
                )
        p = np.vstack(probabilities)
        truth = va.dataset.y
        thresholds = optimize_thresholds(truth, p)
        metrics = evaluate(truth[:, :-1], p[:, :-1], thresholds[:-1])
        history.append(dict(epoch=epoch + 1, loss=float(np.mean(losses)), validation_macro_f1=metrics["macro_f1"]))
        if metrics["macro_f1"] > best:
            best, stale = metrics["macro_f1"], 0
            model.save_pretrained(folder / "best")
            tokenizer.save_pretrained(folder / "best")
            write_json(
                folder / "validation.json",
                dict(
                    metrics=metrics, thresholds=thresholds.tolist(), dataset_version=digest(data), arguments=vars(args)
                ),
            )
        else:
            stale += 1
        torch.save(
            dict(
                model=model.state_dict(),
                optimizer=optimizer.state_dict(),
                scheduler=scheduler.state_dict(),
                scaler=scaler.state_dict(),
                epoch=epoch,
                best=best,
                stale=stale,
                history=history,
                rng=torch.get_rng_state(),
                cuda_rng=torch.cuda.get_rng_state_all() if device.type == "cuda" else [],
                dataset_version=digest(data),
                arguments={k: v for k, v in vars(args).items() if k != "resume"},
            ),
            checkpoint,
        )
        write_json(folder / "history.json", history)
        print(history[-1], flush=True)
        if stale >= args.patience:
            break


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=["xlm-roberta-base", "bert-base-multilingual-cased"], default="xlm-roberta-base")
    p.add_argument("--length", type=int, choices=[128, 256], default=128)
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--patience", type=int, default=2)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--accumulation", type=int, default=4)
    p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--focal", action="store_true")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--allow-cpu", action="store_true")
    main(p.parse_args())
