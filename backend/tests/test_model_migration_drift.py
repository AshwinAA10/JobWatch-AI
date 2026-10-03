"""Regression tests ensuring 100% schema alignment between SQLAlchemy models and Alembic migrations.

Guarantees that `alembic check` / autogenerate detects zero unexpected constraint or index diffs.
"""

import ast
import glob
from sqlalchemy.dialects.postgresql import dialect as pg_dialect
from alembic.autogenerate.api import AutogenContext
from alembic.migration import MigrationContext
from alembic.autogenerate.compare.constraints import _compare_indexes_and_uniques
from alembic.operations.ops import ModifyTableOps

from app.models import Base


def _extract_migration_indexes_and_uniques():
    """Parse all Alembic migration revision files for table unique constraints and index names."""
    migration_files = sorted(glob.glob("backend/alembic/versions/*.py"))
    assert len(migration_files) >= 9, "Expected at least 9 Alembic migration files"

    mig_indexes = {}
    mig_uqs = {}

    for mf in migration_files:
        with open(mf, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            # Capture op.create_index calls
            if isinstance(node, ast.Call) and hasattr(node.func, "attr") and node.func.attr == "create_index":
                ix_arg = node.args[0]
                ix_name = None
                if isinstance(ix_arg, ast.Constant):
                    ix_name = ix_arg.value
                elif isinstance(ix_arg, ast.Call) and ix_arg.args and isinstance(ix_arg.args[0], ast.Constant):
                    # Handle op.f("ix_...")
                    ix_name = ix_arg.args[0].value
                tname = node.args[1].value if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) else None
                if tname and ix_name:
                    mig_indexes.setdefault(tname, set()).add(ix_name)

            # Capture sa.UniqueConstraint in op.create_table calls
            if isinstance(node, ast.Call) and hasattr(node.func, "attr") and node.func.attr == "create_table":
                tname = node.args[0].value if isinstance(node.args[0], ast.Constant) else None
                if tname:
                    for arg in node.args[1:]:
                        if isinstance(arg, ast.Call) and hasattr(arg.func, "attr") and arg.func.attr == "UniqueConstraint":
                            for kw in arg.keywords:
                                if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                                    mig_uqs.setdefault(tname, set()).add(kw.value.value)

    return mig_indexes, mig_uqs


def test_unique_constraints_parity_with_migrations():
    """Verify every UniqueConstraint in migrations is mirrored in SQLAlchemy model metadata."""
    _, mig_uqs = _extract_migration_indexes_and_uniques()

    for table_name, expected_uqs in mig_uqs.items():
        assert table_name in Base.metadata.tables, f"Table {table_name} missing from Base.metadata"
        table = Base.metadata.tables[table_name]
        model_uqs = {c.name for c in table.constraints if c.__class__.__name__ == "UniqueConstraint"}
        
        missing_in_model = expected_uqs - model_uqs
        assert not missing_in_model, (
            f"Table '{table_name}' is missing UniqueConstraints in model metadata: {missing_in_model}. "
            f"Alembic check will attempt to remove these constraints."
        )


def test_indexes_parity_with_migrations():
    """Verify every Index in migrations is mirrored in SQLAlchemy model metadata."""
    mig_indexes, _ = _extract_migration_indexes_and_uniques()

    for table_name, expected_indexes in mig_indexes.items():
        assert table_name in Base.metadata.tables, f"Table {table_name} missing from Base.metadata"
        table = Base.metadata.tables[table_name]
        model_indexes = {i.name for i in table.indexes}
        
        missing_in_model = expected_indexes - model_indexes
        assert not missing_in_model, (
            f"Table '{table_name}' is missing Indexes in model metadata: {missing_in_model}. "
            f"Alembic check will attempt to remove these indexes."
        )

        unexpected_in_model = model_indexes - expected_indexes
        assert not unexpected_in_model, (
            f"Table '{table_name}' has unexpected Indexes in model metadata not in migrations: {unexpected_in_model}. "
            f"Alembic check will attempt to add these indexes."
        )


def test_autogenerate_compare_zero_drift():
    """Verify Alembic's _compare_indexes_and_uniques detects 0 operations across all tables."""
    mig_indexes, mig_uqs = _extract_migration_indexes_and_uniques()
    mc = MigrationContext.configure(dialect=pg_dialect())
    ctx = AutogenContext(mc)

    class SimulatedReflectedInspector:
        def __init__(self):
            self.info_cache = {}

        def get_unique_constraints(self, tname, schema=None):
            uqs = mig_uqs.get(tname, set())
            table = Base.metadata.tables.get(tname)
            result = []
            if table is not None:
                for c in table.constraints:
                    if c.__class__.__name__ == "UniqueConstraint" and c.name in uqs:
                        result.append({"name": c.name, "column_names": [col.name for col in c.columns], "duplicates_index": None})
            return result

        def get_indexes(self, tname, schema=None):
            idxs = mig_indexes.get(tname, set())
            table = Base.metadata.tables.get(tname)
            result = []
            if table is not None:
                for idx in table.indexes:
                    if idx.name in idxs:
                        result.append({"name": idx.name, "column_names": [col.name for col in idx.columns], "unique": idx.unique})
            return result

    ctx.inspector = SimulatedReflectedInspector()

    for tname, table in Base.metadata.tables.items():
        ops = ModifyTableOps(tname, [])
        _compare_indexes_and_uniques(ctx, ops, None, tname, table, table)
        assert len(ops.ops) == 0, f"Alembic detected drift on table {tname}: {ops.ops}"

