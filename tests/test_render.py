from pathlib import Path

RENDER_YAML = Path("render.yaml").read_text()


def test_start_command_binds_render_port_and_never_logs_ips():
    [start] = [line for line in RENDER_YAML.splitlines() if "startCommand:" in line]

    assert "uvicorn backend.main:app" in start
    assert "--host 0.0.0.0 --port $PORT" in start
    assert "--no-access-log" in start  # the access log prints client IPs


def test_uses_free_instance():
    # Render's default when no plan is given is a paid instance.
    assert "plan: free" in RENDER_YAML


def test_every_env_var_is_a_secret_typed_into_render_not_stored_in_git():
    keys = [line.split("=")[0] for line in Path(".env.example").read_text().splitlines() if "=" in line]
    for key in keys:
        assert f"- key: {key}\n        sync: false" in RENDER_YAML
