# Database Migrations Guide

## Overview

This project uses [Alembic](https://alembic.sqlalchemy.org/) for automatic database schema migrations. Alembic tracks changes to your SQLAlchemy models and generates migration scripts automatically.

## Key Benefits

- **Automatic Migration Generation**: Alembic detects changes in your models and creates migration scripts
- **Version Control**: All schema changes are tracked with version history
- **Rollback Support**: Easily revert to previous database states
- **Safe Migrations**: Review migration scripts before applying them
- **CI/CD Ready**: Integrate migrations into your deployment pipeline

## Quick Start

### Initial Setup

The project is already configured with Alembic. When you start the application for the first time, migrations will run automatically.

### Common Workflows

#### 1. Modifying Database Models

When you change a model in `src/task_context_mcp/database/models.py`:

```bash
# 1. Make your changes to the model
# For example, add a new column to TaskContext

# 2. Generate a migration
uv run alembic revision --autogenerate -m "add_new_column_to_task_context"

# 3. Review the generated migration file in alembic/versions/

# 4. Apply the migration
uv run alembic upgrade head
```

**Note**: The application automatically runs migrations on startup, so step 4 is optional during development.

#### 2. Creating a Manual Migration

For complex changes (data migrations, custom SQL):

```bash
# Create an empty migration file
uv run alembic revision -m "custom_data_migration"

# Edit the generated file in alembic/versions/
# Add your custom upgrade() and downgrade() logic

# Apply the migration
uv run alembic upgrade head
```

#### 3. Viewing Migration History

```bash
# Show current database version
uv run alembic current

# Show migration history
uv run alembic history --verbose

# Show pending migrations
uv run alembic heads
```

#### 4. Rolling Back Changes

```bash
# Downgrade one revision
uv run alembic downgrade -1

# Downgrade to a specific revision
uv run alembic downgrade <revision_id>

# Downgrade all the way back
uv run alembic downgrade base
```

## Migration File Structure

Migration files are stored in `alembic/versions/` with date-based naming:

```
2025_12_14_1220-261b037d15fa_initial_schema.py
```

Each file contains:
- `upgrade()`: Forward migration logic
- `downgrade()`: Rollback logic
- Metadata: revision ID, dependencies, timestamps

## Best Practices

### 1. Always Review Generated Migrations

Alembic's autogenerate is smart but not perfect. Always review the generated migration:

```bash
# After generating a migration
cat alembic/versions/<latest_migration>.py
```

Check for:
- Unintended schema changes
- Missing changes (Alembic can't detect everything)
- Destructive operations (DROP TABLE, DROP COLUMN)

### 2. Test Migrations on a Copy

Before applying to production:

```bash
# Test upgrade
uv run alembic upgrade head

# Test downgrade
uv run alembic downgrade -1

# Re-apply
uv run alembic upgrade head
```

### 3. Never Edit Applied Migrations

Once a migration is applied (especially in production), never modify it. Instead:

```bash
# Create a new migration to fix the issue
uv run alembic revision --autogenerate -m "fix_previous_migration"
```

### 4. Use Descriptive Migration Messages

```bash
# Good
uv run alembic revision --autogenerate -m "add_priority_field_to_artifacts"

# Bad
uv run alembic revision --autogenerate -m "update"
```

### 5. Handling Data Migrations

When changing column types or structure, consider data migration:

```python
def upgrade() -> None:
    """Upgrade schema."""
    # Add new column
    op.add_column('artifacts', sa.Column('priority', sa.Integer(), nullable=True))
    
    # Migrate data
    op.execute("UPDATE artifacts SET priority = 1 WHERE status = 'active'")
    
    # Make column non-nullable
    op.alter_column('artifacts', 'priority', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('artifacts', 'priority')
```

## What Alembic Can and Cannot Detect

### ✅ Alembic CAN Detect:
- New tables
- Removed tables
- New columns
- Removed columns
- Column type changes
- Nullable changes
- Default value changes
- Foreign key constraints
- Indexes

### ❌ Alembic CANNOT Detect:
- Table or column renames (appears as drop + add)
- Changes to server defaults
- Enum value changes
- Check constraints (SQLite limitation)
- Custom SQL operations

For these cases, create manual migrations.

## SQLite-Specific Considerations

This project uses SQLite with batch mode enabled for migrations. SQLite has limitations:

- No direct ALTER COLUMN support
- Foreign keys must be disabled during migrations
- Batch mode recreates tables for schema changes

Alembic handles this automatically with `render_as_batch=True` in `alembic/env.py`.

## Integration with Application

### Automatic Migrations on Startup

The `DatabaseManager.init_db()` method automatically runs migrations:

```python
from task_context_mcp.database.database import DatabaseManager

db_manager = DatabaseManager()
db_manager.init_db()  # Runs migrations automatically
```

### Programmatic Migration Control

You can also run migrations programmatically:

```python
from task_context_mcp.database.migrations import (
    run_migrations,
    create_migration,
    downgrade_migration,
)

# Run all pending migrations
run_migrations()

# Create a new migration
create_migration("add_new_feature", autogenerate=True)

# Rollback one step
downgrade_migration("-1")
```

## Troubleshooting

### "Can't locate revision identified by '<id>'"

Your database is out of sync with migration files. Options:

```bash
# Option 1: Stamp the database with current state
uv run alembic stamp head

# Option 2: Start fresh (WARNING: deletes data)
rm ~/.task-context-mcp/data/task_context.db
# Restart the application
```

### "Target database is not up to date"

Run pending migrations:

```bash
uv run alembic upgrade head
```

### Alembic Can't Find Models

Ensure `alembic/env.py` correctly imports your models:

```python
from task_context_mcp.database.models import Base
target_metadata = Base.metadata
```

### Migration Conflicts

If multiple developers create migrations simultaneously:

```bash
# Merge migrations
uv run alembic merge <rev1> <rev2> -m "merge_branches"
```

## CI/CD Integration

### In Your Deployment Pipeline

```bash
# Run migrations before starting the application
uv run alembic upgrade head

# Start the application
uv run task-context-mcp
```

### Docker Example

```dockerfile
# In your Dockerfile entrypoint
CMD ["sh", "-c", "uv run alembic upgrade head && uv run task-context-mcp"]
```

## Further Reading

- [Alembic Official Documentation](https://alembic.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Auto Generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [SQLite Batch Mode](https://alembic.sqlalchemy.org/en/latest/batch.html)

## Getting Help

For issues with migrations:

1. Check this guide first
2. Review Alembic logs: `uv run alembic upgrade head --verbose`
3. Open an issue on GitHub with migration details
