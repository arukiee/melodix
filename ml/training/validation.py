"""Validation helpers used for model selection, never test data."""

import torch

from ml.evaluation.metrics import binary_metrics
from ml.models.transcription.losses import transcription_loss


@torch.no_grad()
def validate_model(model, loader, device, config) -> dict[str, float]:
    model.eval()
    predictions, labels = [], []
    total_loss = 0.0
    batches = 0
    for features, batch_labels in loader:
        features = features.to(device)
        batch_labels = {key: value.to(device) for key, value in batch_labels.items()}
        outputs = model(features)
        loss, _ = transcription_loss(outputs, batch_labels, config)
        total_loss += loss.item()
        batches += 1
        output = outputs["onset"].cpu() >= config["onset_threshold"]
        predictions.extend(output.flatten().int().tolist())
        labels.extend((batch_labels["onset"] >= 0.5).flatten().int().tolist())
    metrics = binary_metrics(predictions, labels)
    return {"validation_loss": total_loss / batches if batches else 0.0, "onset_precision": metrics.precision, "onset_recall": metrics.recall, "onset_f1": metrics.f1}