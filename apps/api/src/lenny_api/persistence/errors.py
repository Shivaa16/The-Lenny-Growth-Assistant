from sqlalchemy.exc import SQLAlchemyError

# asyncpg can surface connection establishment failures as raw OSError subclasses before
# SQLAlchemy wraps them. Repository boundaries normalize both families into product errors.
DATABASE_OPERATION_ERRORS = (SQLAlchemyError, OSError)
