from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


SUPPORTED = {".csv", ".xlsx", ".md"}


class DatasetIngestor:
    """Convert human-friendly training files into conversational JSONL."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def build_jsonl(self) -> dict[str, Any]:
        records: list[dict[str, Any]] = []
        source_files: list[str] = []
        for path in sorted(self.root.iterdir()):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED:
                continue
            source_files.append(path.name)
            records.extend(self._read(path))

        output = self.root / "normalized.jsonl"
        with output.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        return {"jsonl_path": str(output), "records": len(records), "source_files": source_files}

    def _read(self, path: Path) -> list[dict[str, Any]]:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                return [self._row(row) for row in csv.DictReader(handle)]
        if suffix == ".xlsx":
            import pandas as pd
            frame = pd.read_excel(path)
            return [self._row(row) for row in frame.fillna("").to_dict(orient="records")]
        return self._markdown(path)

    @staticmethod
    def _row(row: dict[str, Any]) -> dict[str, Any]:
        prompt = str(row.get("prompt") or row.get("question") or row.get("input") or "").strip()
        completion = str(row.get("completion") or row.get("answer") or row.get("response") or row.get("output") or "").strip()
        if not prompt or not completion:
            raise ValueError("Training rows must contain prompt/question/input and completion/answer/response/output")
        return {"messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": completion}]}

    @staticmethod
    def _markdown(path: Path) -> list[dict[str, Any]]:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        records = []
        for block in blocks:
            if "\n---\n" in block:
                prompt, completion = block.split("\n---\n", 1)
            elif "\nAnswer:\n" in block:
                prompt, completion = block.split("\nAnswer:\n", 1)
            else:
                continue
            records.append({"messages": [{"role": "user", "content": prompt.replace("Question:", "", 1).strip()}, {"role": "assistant", "content": completion.strip()}]})
        return records
