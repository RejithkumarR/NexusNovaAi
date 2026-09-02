from unittest.mock import patch

import pytest

from nova.code_agent import DockerCodeSandbox
from nova.local_model import LocalTransformerModel


def test_local_model_requires_local_checkpoint(monkeypatch):
    monkeypatch.delenv("NOVA_MODEL_PATH", raising=False)
    model = LocalTransformerModel(model_path=None)
    with pytest.raises(RuntimeError, match="NOVA_MODEL_PATH"):
        model.generate("hello")


def test_code_sandbox_builds_networkless_docker_command(monkeypatch):
    class Completed:
        stdout = "ok\n"
        stderr = ""
        returncode = 0

    with patch("nova.code_agent.subprocess.run", return_value=Completed()) as run:
        result = DockerCodeSandbox(image="test-sandbox").run_python("print('ok')")

    assert result.stdout == "ok\n"
    command = run.call_args.args[0]
    assert "--network" in command
    assert "none" in command
    assert "--cap-drop" in command
    assert "ALL" in command
    assert "test-sandbox" in command
