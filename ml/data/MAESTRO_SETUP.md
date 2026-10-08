# MAESTRO setup

1. Download MAESTRO from the official Magenta/Zenodo distribution and review its license and attribution terms before use.
2. Extract it outside Git-tracked source or into `ml/data/raw/MAESTRO/`. Do not commit WAV/MIDI files.
  Plan for at least 200 GB of free disk space for the full archive, extracted files, feature caches, checkpoints, and reports; confirm the current release size before downloading.
3. Preserve the official train/validation/test split from the metadata. Never move test recordings into train or validation.
4. Build a manifest:

```sh
python ml/data/build_manifest.py \
  --root ml/data/raw/MAESTRO \
  --metadata ml/data/raw/MAESTRO/maestro-v3.0.0.json \
  --output ml/data/manifests/maestro.csv
```

Before training, validate every manifest row: audio and MIDI paths must exist, the metadata split must be one of `train`, `validation`, or `test`, and paired audio/MIDI durations must agree within the configured tolerance. Reject rows with missing pairs instead of silently assigning them to another split.

For a smoke experiment, use a small train-only/validation-only subset after verifying each row's split. `--limit` limits the manifest rows but does not create missing split records; the resulting CSV must still contain both train and validation rows before training.

The manifest records file ID, paired audio/MIDI paths, official split, duration, sample rate, preprocessing version, dataset version, and augmentation metadata. Test data is consumed only by `evaluate_transcription.py` after checkpoint selection.

Reproducible training environment:

```sh
docker compose -f docker-compose.training.yml build ml_training
```

The training image is Python 3.12 and installs `requirements.lock`, including CPU PyTorch wheels. Docker CPU mode is the reproducible baseline. Full GPU training requires a separately configured NVIDIA CUDA Docker runtime. Native macOS MPS is optional and must be tested separately with `--device mps`; never assume acceleration without runtime detection.

Run the non-research smoke pipeline first:

```sh
docker compose -f docker-compose.training.yml run --rm ml_training
```

This checks model construction, one epoch, validation, and checkpoint writing using synthetic tensors. It is not a metric result and does not replace MAESTRO evaluation. A real MAESTRO run requires the manifest and actual WAV/MIDI files.
