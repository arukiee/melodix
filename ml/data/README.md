# Research data policy

Place legally obtained MAESTRO files under `ml/data/raw/`. Do not commit audio or MIDI datasets. Generated manifests belong in `ml/data/manifests/` and must record the official MAESTRO train/validation/test split, source paths, duration, sample rate, preprocessing version, and augmentation metadata.

The test split is reserved for one final evaluation. Training and tuning use only train and validation records.
