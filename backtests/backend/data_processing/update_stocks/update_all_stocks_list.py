import traceback
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_processing.data_provider.tushare import Tushare
from end_points.init_global import init_global
from end_points.config.global_var import global_var



def update_stocks_list(db):
    try:
        data_tool = Tushare()
        data_tool.update_all_stocks_list(db)

    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        print(err)
        print(datetime.now())
    return

if __name__ == '__main__':
    env_dist = os.environ
    config_file = env_dist.get('CFG_PATH', '../../service.conf')
    init_global(config_file)
    db = global_var["db"]
    update_stocks_list(db)
