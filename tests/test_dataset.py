from pathlib import Path

from nova.dataset import DatasetIngestor


def test_csv_dataset_is_normalized(tmp_path: Path):
    (tmp_path / "train.csv").write_text("prompt,completion\nhello,world\n", encoding="utf-8")
    result = DatasetIngestor(tmp_path).build_jsonl()
    assert result["records"] == 1
    assert '"role": "user"' in (tmp_path / "normalized.jsonl").read_text(encoding="utf-8")


def test_markdown_dataset_is_normalized(tmp_path: Path):
    (tmp_path / "train.md").write_text("Question: hello\n---\nworld\n", encoding="utf-8")
    result = DatasetIngestor(tmp_path).build_jsonl()
    assert result["records"] == 1
