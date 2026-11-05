import pytest

import guance_agent.cli as cli
import guance_agent.config as config
import guance_agent.main as main_mod
import guance_agent.orchestrator as orchestrator
from guance_agent.config import Settings
from guance_agent.schemas import TaskRequest


@pytest.fixture(autouse=True)
def _isolate_dotenv(monkeypatch, tmp_path):
    """测试不读取本机的环境配置文件。"""
    blank = tmp_path / "absent.env"
    real = config.load_settings

    def patched(env_file=None):
        return real(env_file=blank)

    for module in (config, main_mod, orchestrator, cli):
        if hasattr(module, "load_settings"):
            monkeypatch.setattr(module, "load_settings", patched)


@pytest.fixture
def env(tmp_path):
    settings = Settings(
        kb_backend="mock",
        session_path=tmp_path / "sessions.sqlite",
        run_log=tmp_path / "runs.jsonl",
    )
    task = TaskRequest(
        run_id="run_test",
        session_id="s_test",
        question="甲市农业重点",
        created_at="2026-10-23T00:00:00Z",
    )
    return settings, task
