# Melodix Research ML Track

## Status

The repository now contains a custom frequency-aware CNN-BiLSTM architecture with independent sigmoid onset, frame, offset, and velocity heads; canonical target/event contracts; a deterministic keyboard/MIDI baseline; measured metric helpers; and an isolated FastAPI ML service.

No model accuracy is reported yet. PyTorch is not installed in the current backend virtual environment, no MAESTRO files are checked into the repository, and no trained checkpoint exists. The service deliberately returns `503` for transcription until a real checkpoint is produced.

## Dataset policy

Use the official MAESTRO train/validation/test split. Store obtained files only under `ml/data/raw/` and never commit them. Manifests must include source paths, duration, split, sample rate, preprocessing version, augmentation metadata, and a dataset version. Reserve test data for the final report. ASAP may be added only after licensing and permitted-file review.

## Run the research track

1. Install `ml/requirements.txt` in a dedicated Python environment with a compatible PyTorch build.
2. Place MAESTRO audio/MIDI under `ml/data/raw/` and generate a manifest under `ml/data/manifests/`.
3. Implement/execute tensorization and run `python ml/training/train_transcription.py --manifest <manifest>`.
4. Save the best validation checkpoint under `ml/checkpoints/` and run held-out evaluation to create CSV/JSON reports under `ml/reports/`.
5. Start `uvicorn ml.inference.app:app --port 8100` only with a measured checkpoint.

## Research boundaries

Keyboard and MIDI matching remain deterministic baselines. The ML service handles microphone transcription only. Scoring consumes validated note events and calculates music facts; Ollama, when connected, may explain those facts but must not detect notes, calculate scores, or access raw audio/database records.

## Planned comparisons

The evaluation harness should compare deterministic keyboard/MIDI against microphone CNN-BiLSTM, CNN-only against CNN+BiLSTM, standard against frequency-aware branches, and clean-only against noise/reverb/EQ augmentation using the same held-out test split. Results must be generated from the scripts, never entered manually.
