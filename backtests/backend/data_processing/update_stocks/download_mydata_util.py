from db.models_dynamic import (
    record_table_attr,
    cn_index_table_attr,
    cn_stock_table_attr,
    DynamicBase
)


def create_stock_table(db, table_name, bind_key):
    """Create a stock table dynamically using SQLAlchemy"""
    if 's' in table_name:
        attr_dict = cn_index_table_attr(table_name, bind_key)
    else:
        attr_dict = cn_stock_table_attr(table_name, bind_key)

    # Use DynamicBase instead of db.Model for pure SQLAlchemy
    NewClass = type(table_name, (DynamicBase,), attr_dict)

    # Get the correct engine for the bind_key
    if hasattr(db, 'get_engine'):
        engine = db.get_engine(bind_key)
    elif hasattr(db, 'db_engine'):
        engine = db.db_engine
    else:
        engine = db.engine

    # Create table using SQLAlchemy engine
    # IMPORTANT: Pass tables=[NewClass.__table__] to ensure this specific table is created
    DynamicBase.metadata.create_all(bind=engine, tables=[NewClass.__table__], checkfirst=True)

    return NewClass


def get_stock_table(db, table_name, bind_key):
    """Get a stock table class without creating it"""
    if 's' in table_name:
        attr_dict = cn_index_table_attr(table_name, bind_key)
    else:
        attr_dict = cn_stock_table_attr(table_name, bind_key)

    # Use DynamicBase instead of db.Model for pure SQLAlchemy
    NewClass = type(table_name, (DynamicBase,), attr_dict)
    return NewClass


def create_record_table(db, table_name, bind_key):
    """Create a record table dynamically using SQLAlchemy"""
    attr_dict = record_table_attr(table_name, bind_key)

    # Use DynamicBase instead of db.Model for pure SQLAlchemy
    NewClass = type(table_name, (DynamicBase,), attr_dict)

    # Get the correct engine for the bind_key
    if hasattr(db, 'get_engine'):
        engine = db.get_engine(bind_key)
    elif hasattr(db, 'db_engine'):
        engine = db.db_engine
    else:
        engine = db.engine

    # Create table using SQLAlchemy engine
    # IMPORTANT: Pass tables=[NewClass.__table__] to ensure this specific table is created
    DynamicBase.metadata.create_all(bind=engine, tables=[NewClass.__table__], checkfirst=True)

    return NewClass
