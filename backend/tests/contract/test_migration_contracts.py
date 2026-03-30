"""Migration contract tests for Alembic revision hygiene and chain integrity."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from alembic.config import Config
from alembic.script import ScriptDirectory


VERSIONS_DIR = Path(__file__).resolve().parents[2] / "alembic" / "versions"
ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def migration_files() -> list[Path]:
    return sorted(
        path for path in VERSIONS_DIR.glob("*.py") if path.name != "__init__.py"
    )


def load_migration_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def script_directory() -> ScriptDirectory:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", "alembic")
    return ScriptDirectory.from_config(config)


class TestMigrationContracts:
    def test_all_migrations_define_upgrade_and_downgrade(self) -> None:
        for path in migration_files():
            module = load_migration_module(path)

            assert callable(getattr(module, "upgrade", None)), path.name
            assert callable(getattr(module, "downgrade", None)), path.name

    def test_all_revisions_are_unique(self) -> None:
        revisions = [load_migration_module(path).revision for path in migration_files()]

        assert len(revisions) == len(set(revisions))

    def test_single_migration_head_exists(self) -> None:
        assert len(script_directory().get_heads()) == 1

    def test_all_down_revisions_reference_known_parents(self) -> None:
        modules = [load_migration_module(path) for path in migration_files()]
        revisions = {module.revision for module in modules}

        for module in modules:
            down_revision = getattr(module, "down_revision", None)
            if down_revision is None:
                continue
            parents = (
                down_revision
                if isinstance(down_revision, tuple | list)
                else [down_revision]
            )
            for parent in parents:
                assert parent in revisions

    def test_walk_revisions_covers_every_migration_file(self) -> None:
        walked = list(script_directory().walk_revisions())

        assert len(walked) == len(migration_files())
