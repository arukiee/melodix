"""Train the custom CNN-BiLSTM model; requires a prepared MAESTRO manifest."""

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError as exc:
        raise RuntimeError("Install ml/requirements.txt before training") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="ml/configs/transcription.yaml")
    parser.add_argument("--manifest")
    parser.add_argument("--smoke", action="store_true", help="Run one tiny synthetic epoch; not a research result")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda", "mps"), default=None)
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text())
    seed_everything(int(config["seed"]))
    try:
        import torch
        from torch.utils.data import DataLoader
        from ml.models.transcription.cnn_bilstm import FrequencyAwareCNNBiLSTM
        from ml.models.transcription.losses import transcription_loss
        from ml.training.dataset import ManifestDataset, SyntheticSmokeDataset
    except ImportError as exc:
        raise RuntimeError("Install ml/requirements.txt before training") from exc

    if args.smoke:
        train_data = SyntheticSmokeDataset(config, size=2)
        validation_data = SyntheticSmokeDataset(config, size=1)
    else:
        if not args.manifest:
            raise ValueError("--manifest is required unless --smoke is used")
        manifest = Path(args.manifest)
        if not manifest.exists():
            raise FileNotFoundError(manifest)
        train_data = ManifestDataset(manifest, config, split="train")
        validation_data = ManifestDataset(manifest, config, split="validation")
        if not train_data or not validation_data:
            raise ValueError("Manifest must contain both train and validation records")
    from ml.training.device import resolve_device
    requested_device = args.device or config.get("device", "auto")
    device = resolve_device(requested_device)
    model = FrequencyAwareCNNBiLSTM(frequency_bins=int(config["n_mels"])).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"])
    loader = DataLoader(train_data, batch_size=int(config["batch_size"]), shuffle=True)
    validation_loader = DataLoader(validation_data, batch_size=int(config["batch_size"]))
    best_f1 = -1.0
    stale_epochs = 0
    checkpoint_dir = Path("ml/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    epoch_limit = 1 if args.smoke else int(config["epochs"])
    for epoch in range(epoch_limit):
        model.train()
        for features, labels in loader:
            features, labels = features.to(device), {key: value.to(device) for key, value in labels.items()}
            optimizer.zero_grad(set_to_none=True)
            loss, _ = transcription_loss(model(features), labels, config)
            loss.backward()
            optimizer.step()
        from ml.training.validation import validate_model
        metrics = validate_model(model, validation_loader, device, config)
        print({"epoch": epoch + 1, **metrics})
        if metrics["onset_f1"] > best_f1:
            best_f1, stale_epochs = metrics["onset_f1"], 0
            manifest_hash = hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest() if args.manifest else "synthetic-smoke"
            metadata = {
                "architecture_version": "frequency_aware_cnn_bilstm_v1",
                "spectrogram_config": {key: config[key] for key in ("sample_rate", "n_fft", "hop_length", "n_mels", "f_min", "f_max")},
                "frequency_bands": ["low", "mid", "high"],
                "random_seed": config["seed"],
                "dataset_manifest_hash": manifest_hash,
                "epoch": epoch + 1,
                "validation_loss": metrics["validation_loss"],
                "validation_metrics": metrics,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "selected_device": str(device),
                "pipeline_status": "smoke_test_only" if args.smoke else "training_checkpoint",
            }
            torch.save({"model": model.state_dict(), "config": config, "metrics": metrics, "metadata": metadata, "seed": config["seed"], "experiment_id": config["experiment_id"]}, checkpoint_dir / "best.pt")
            (checkpoint_dir / "best.metadata.json").write_text(json.dumps(metadata, indent=2))
        else:
            stale_epochs += 1
            if stale_epochs >= int(config["patience"]):
                break


if __name__ == "__main__":
    main()
