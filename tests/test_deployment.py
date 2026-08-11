from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_container_is_non_root_and_exposes_healthcheck() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "USER nexus" in dockerfile
    assert "EXPOSE 8000" in dockerfile
    assert "/health" in dockerfile
    assert "uvicorn" in dockerfile


def test_docker_build_context_excludes_local_secrets_and_caches() -> None:
    ignore = (ROOT / ".dockerignore").read_text().splitlines()
    assert ".env" in ignore
    assert ".git" in ignore
    assert ".pytest_cache" in ignore


def test_compose_has_restart_policy_and_healthcheck() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()
    assert "restart: unless-stopped" in compose
    assert "healthcheck:" in compose
    assert '"8000:8000"' in compose
