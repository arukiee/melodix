"""Measured frame and note metrics for held-out transcription evaluation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BinaryMetrics:
    precision: float
    recall: float
    f1: float


def binary_metrics(predictions: list[int], labels: list[int]) -> BinaryMetrics:
    if len(predictions) != len(labels):
        raise ValueError("predictions and labels must have equal length")
    true_positive = sum(prediction == label == 1 for prediction, label in zip(predictions, labels))
    predicted_positive = sum(predictions)
    actual_positive = sum(labels)
    precision = true_positive / predicted_positive if predicted_positive else 0.0
    recall = true_positive / actual_positive if actual_positive else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return BinaryMetrics(precision, recall, f1)


def note_onset_metrics(predicted: set[tuple[int, int]], reference: set[tuple[int, int]]) -> BinaryMetrics:
    return binary_metrics(
        [int(item in predicted) for item in sorted(predicted | reference)],
        [int(item in reference) for item in sorted(predicted | reference)],
    )
