"""Unit test verifying Alembic migration 0009_application_tracking upgrade and downgrade functions."""

import importlib.util
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine


def test_migration_0009_metadata():
    """Verify revision and down_revision match Alembic chain."""
    spec = importlib.util.spec_from_file_location(
        "migration_0009",
        "backend/alembic/versions/0009_application_tracking.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert mod.revision == "0009_application_tracking"
    assert mod.down_revision == "0008_saved_jobs"
    assert hasattr(mod, "upgrade")
    assert hasattr(mod, "downgrade")


def test_migration_0009_upgrade_and_downgrade_calls():
    """Verify op calls in upgrade and downgrade execute expected schema operations."""
    spec = importlib.util.spec_from_file_location(
        "migration_0009",
        "backend/alembic/versions/0009_application_tracking.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with patch.object(mod, "op") as mock_op:
        # Test upgrade
        mod.upgrade()
        # Verify 4 tables created: applications, application_history, application_notes, interviews
        created_tables = [call.args[0] for call in mock_op.create_table.call_args_list]
        assert "applications" in created_tables
        assert "application_history" in created_tables
        assert "application_notes" in created_tables
        assert "interviews" in created_tables

        # Test downgrade
        mod.downgrade()
        dropped_tables = [call.args[0] for call in mock_op.drop_table.call_args_list]
        assert "interviews" in dropped_tables
        assert "application_notes" in dropped_tables
        assert "application_history" in dropped_tables
        assert "applications" in dropped_tables
