#!/usr/bin/env python
"""
创建所有数据库表
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from end_points.init_global import init_global
from end_points.config.global_var import global_var
from db.models import Base

def create_tables():
    """创建所有表"""
    try:
        # 初始化数据库连接
        config_file = os.path.join(os.path.dirname(__file__), '..', 'service.conf')
        init_global(config_file)
        db = global_var['db']

        # 创建所有表
        print("正在创建数据库表...")
        Base.metadata.create_all(bind=db.engine)
        print("✅ 所有表创建完成!")
        return True

    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)
