from __future__ import annotations

import base64
import os
from pathlib import Path

import httpx


class GitHubDatasetPublisher:
    """Publishes uploaded datasets using a server-side GitHub token."""

    def __init__(self, token: str, repository: str, branch: str = "feature/nova-foundation"):
        self.token = token
        self.repository = repository
        self.branch = branch

    @classmethod
    def from_environment(cls) -> "GitHubDatasetPublisher | None":
        token = os.getenv("NOVA_GITHUB_TOKEN")
        repository = os.getenv("NOVA_GITHUB_REPOSITORY", "RejithkumarR/Nova")
        branch = os.getenv("NOVA_GITHUB_BRANCH", "feature/nova-foundation")
        return cls(token, repository, branch) if token else None

    def publish_file(self, local_path: Path) -> None:
        content = base64.b64encode(local_path.read_bytes()).decode("ascii")
        repo_path = f"datasets/uploads/{local_path.name}"
        url = f"https://api.github.com/repos/{self.repository}/contents/{repo_path}"
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json"}
        with httpx.Client(timeout=30) as client:
            existing = client.get(url, headers=headers, params={"ref": self.branch})
            payload = {"message": f"data: add training dataset {local_path.name}", "content": content, "branch": self.branch}
            if existing.status_code == 200:
                payload["sha"] = existing.json()["sha"]
            response = client.put(url, headers=headers, json=payload)
            response.raise_for_status()
