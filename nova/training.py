from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def start_training(*, model_name: str, dataset_path: str, output_dir: str, num_train_epochs: float) -> dict:
    script = Path(__file__).with_name("train_sft.py")
    env = os.environ.copy()
    env.update({"NOVA_MODEL_NAME": model_name, "NOVA_DATASET": dataset_path, "NOVA_OUTPUT": output_dir, "NOVA_EPOCHS": str(num_train_epochs)})
    process = subprocess.Popen([sys.executable, str(script)], env=env)
    return {"status": "started", "pid": process.pid, "model": model_name, "dataset": dataset_path, "output_dir": output_dir}
