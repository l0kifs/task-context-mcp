from unittest.mock import MagicMock

import pytest
from alembic.config import Config

import task_context_mcp.database.migrations as migrations


def test_get_alembic_config_returns_config():
    cfg = migrations.get_alembic_config()
    assert isinstance(cfg, Config)
    assert cfg.config_file_name is not None
    assert "alembic.ini" in str(cfg.config_file_name)


def test_get_alembic_config_missing(monkeypatch):
    # Simulate missing alembic.ini by forcing Path.exists to return False
    monkeypatch.setattr("pathlib.Path.exists", lambda self: False)
    with pytest.raises(FileNotFoundError):
        migrations.get_alembic_config()


def test_run_migrations_calls_upgrade(monkeypatch):
    mock_upgrade = MagicMock()
    monkeypatch.setattr(migrations.command, "upgrade", mock_upgrade)

    migrations.run_migrations()

    assert mock_upgrade.called
    # head should be the second argument
    assert mock_upgrade.call_args.args[1] == "head"


def test_run_migrations_propagates_exception(monkeypatch):
    def raise_err(cfg, rev):
        raise RuntimeError("boom")

    monkeypatch.setattr(migrations.command, "upgrade", raise_err)
    with pytest.raises(RuntimeError):
        migrations.run_migrations()


def test_create_migration_autogenerate_true(monkeypatch):
    mock_revision = MagicMock()
    monkeypatch.setattr(migrations.command, "revision", mock_revision)

    migrations.create_migration("msg", autogenerate=True)

    assert mock_revision.called
    kwargs = mock_revision.call_args.kwargs
    # autogenerate should be passed and True
    assert kwargs.get("message") == "msg"
    assert kwargs.get("autogenerate") is True


def test_create_migration_autogenerate_false(monkeypatch):
    mock_revision = MagicMock()
    monkeypatch.setattr(migrations.command, "revision", mock_revision)

    migrations.create_migration("msg", autogenerate=False)

    assert mock_revision.called
    kwargs = mock_revision.call_args.kwargs
    assert kwargs.get("message") == "msg"
    # autogenerate should not be in kwargs when False
    assert "autogenerate" not in kwargs


def test_create_migration_raises_on_error(monkeypatch):
    def raise_err(cfg, message=None, autogenerate=None):
        raise RuntimeError("boom2")

    monkeypatch.setattr(migrations.command, "revision", raise_err)
    with pytest.raises(RuntimeError):
        migrations.create_migration("msg", autogenerate=True)


def test_downgrade_migration_calls_downgrade(monkeypatch):
    mock_down = MagicMock()
    monkeypatch.setattr(migrations.command, "downgrade", mock_down)

    migrations.downgrade_migration(revision="base")

    assert mock_down.called
    assert mock_down.call_args.args[1] == "base"


def test_downgrade_migration_raises_on_error(monkeypatch):
    def raise_err(cfg, rev):
        raise RuntimeError("boom3")

    monkeypatch.setattr(migrations.command, "downgrade", raise_err)
    with pytest.raises(RuntimeError):
        migrations.downgrade_migration(revision="-1")


def test_get_current_revision_returns_none_on_failure(monkeypatch):
    monkeypatch.setattr(
        migrations,
        "get_alembic_config",
        lambda: (_ for _ in ()).throw(RuntimeError("no cfg")),
    )
    result = migrations.get_current_revision()
    assert result is None
