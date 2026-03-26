import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from db.models_dynamic import get_stock_model
from end_points.common.const.consts import DataBase
from end_points.config.db_init import resolve_database_config
from end_points.get_stock.operations.get_stock_utils import get_all_stocks
from end_points.init_global import load_runtime_config

def transform_config(config_file):
    runtime_config = load_runtime_config(config_file)
    return resolve_database_config(runtime_config)

def init_session(config, bind_key=DataBase.ai_stock):
    database_uri = config['main_uri'] if bind_key == DataBase.ai_stock else config['bind_uris'].get(bind_key, config['main_uri'])
    try:
        engine = create_engine(database_uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        print("init database session")
    except Exception as e:
        print(e)
    return session


def remove_stale_stocks(config):
    try:
        engine = init_engine(config)
        inspection = inspect(engine)
        all_tables = inspection.get_table_names()
        ai_stock_session = init_session(config, DataBase.ai_stock)
        all_stocks = get_all_stocks(ai_stock_session)

        with engine.connect() as connection:
            trans = connection.begin()
            try:
                for stock_code in all_tables:
                    if stock_code not in all_stocks:
                        stock_class = get_stock_model(stock_code)
                        stock_class.__table__.drop(engine, checkfirst=True)
                        print("deleted table for stock: {}".format(stock_code))
                trans.commit()
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        print(e)
    finally:
        print("closing database")
        engine.dispose()
        ai_stock_session.close()
    return

def init_engine(config, bind_key=DataBase.stocks):
    database_uri = config['bind_uris'].get(bind_key, config['main_uri'])
    try:
        engine = create_engine(database_uri)
        print("init database")
    except Exception as e:
        print(e)
    return engine

if __name__ == '__main__':
    env_dist = os.environ
    config_file = env_dist.get('CFG_PATH', '../../service.conf')
    config = transform_config(config_file)
    remove_stale_stocks(config)
