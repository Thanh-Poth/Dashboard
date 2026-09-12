from pathlib import Path
import yaml

def load_config(path: str = "config.yaml") -> dict:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file NOT found : {file_path.resolve()}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}