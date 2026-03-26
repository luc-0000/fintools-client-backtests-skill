#!/usr/bin/env python
# encoding=utf8
"""
数据库导出脚本

支持功能：
1. SQLite 模式导出数据库文件副本
2. MySQL 模式导出 mysqldump 文件
3. 导出为 JSON 文件（便于查看和部分恢复）
4. 自动按时间戳命名导出文件

使用方法：
    python scripts/export_database.py                    # 导出为 SQL 和 JSON
    python scripts/export_database.py --sql-only         # 仅导出 SQL
    python scripts/export_database.py --json-only        # 仅导出 JSON
    python scripts/export_database.py --output-dir ./backups
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from end_points.config.db_init import resolve_database_config
from end_points.init_global import init_global, load_runtime_config
from end_points.config.global_var import global_var
from db.models import (
    Stock, StockIndex, UpdatingStock, StocksInPool,
    Pool, PoolStock, Rule, RulePool, StockRuleEarn, PoolRuleEarn,
    Simulator, SimTrading, SimulatorConfig, AgentTrading
)


def get_db_config(config_file='../../service.conf'):
    """从运行时配置中获取数据库连接信息。"""
    config = load_runtime_config(config_file)
    resolved = resolve_database_config(config)
    db_config = {
        'backend': resolved['backend'],
        'database': resolved['database_path'].name if resolved['backend'] == 'sqlite' else config.get('MYSQL_DATABASE', 'fintools_backtest'),
        'main_uri': resolved['main_uri'],
        'runtime_config': config,
    }
    if resolved['backend'] == 'sqlite':
        db_config['sqlite_path'] = resolved['database_path']
    else:
        db_config.update({
            'host': config.get('MYSQL_HOST', 'localhost'),
            'port': int(config.get('MYSQL_PORT', 3306)),
            'user': config.get('MYSQL_USER', 'root'),
            'password': config.get('MYSQL_PASSWORD', ''),
        })
    return db_config


def export_to_sql(db_config, output_file):
    """导出当前配置对应的数据库快照。"""
    if db_config['backend'] == 'sqlite':
        sqlite_path = Path(db_config['sqlite_path'])
        if not sqlite_path.exists():
            print(f"❌ SQLite 数据库不存在: {sqlite_path}")
            return False

        print(f"🔧 正在导出 SQLite 数据库副本: {output_file}")
        Path(output_file).write_bytes(sqlite_path.read_bytes())
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"✅ SQLite 导出成功! 文件大小: {file_size:.2f} MB")
        return True

    print(f"🔧 正在导出 MySQL 数据库到 SQL 文件: {output_file}")
    cmd = [
        'mysqldump',
        f'-h{db_config["host"]}',
        f'-P{db_config["port"]}',
        f'-u{db_config["user"]}',
        f'-p{db_config["password"]}',
        '--single-transaction',
        '--quick',
        '--lock-tables=false',
        '--routines',
        '--triggers',
        '--events',
        db_config['database'],
    ]
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=True)
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"✅ MySQL 导出成功! 文件大小: {file_size:.2f} MB")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ MySQL 导出失败: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ 未找到 mysqldump，请安装 MySQL 客户端工具")
        return False


def export_table_to_json(db_session, table_class, table_name, output_dir):
    """导出单个表为 JSON 文件"""
    print(f"  📋 导出表: {table_name}")

    try:
        # 查询所有数据
        records = db_session.query(table_class).all()

        # 转换为字典列表
        data = []
        for record in records:
            record_dict = {}
            for c in record.__table__.columns:
                value = getattr(record, c.name)
                # 处理 datetime 对象
                if isinstance(value, datetime):
                    value = value.isoformat()
                record_dict[c.name] = value
            data.append(record_dict)

        # 写入 JSON 文件
        output_file = os.path.join(output_dir, f"{table_name}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"    ✅ {table_name}: {len(data)} 条记录")
        return len(data)

    except Exception as e:
        print(f"    ❌ {table_name} 导出失败: {str(e)}")
        return 0


def export_to_json(db_config, output_dir):
    """使用 SQLAlchemy 导出所有表为 JSON 文件"""
    print(f"📊 正在导出数据库到 JSON 目录: {output_dir}")

    # 初始化数据库连接
    try:
        init_global(db_config['runtime_config'].get('_SERVICE_CONFIG_PATH'))
        db = global_var["db"]

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 定义要导出的表
        tables = [
            (Stock, 'stock'),
            (StockIndex, 'stock_index'),
            (UpdatingStock, 'updating_stock'),
            (StocksInPool, 'stocks_in_pool'),
            (Pool, 'pool'),
            (PoolStock, 'pool_stock'),
            (Rule, 'rule'),
            (RulePool, 'rule_pool'),
            (StockRuleEarn, 'stock_rule_earn'),
            (PoolRuleEarn, 'pool_rule_earn'),
            (Simulator, 'simulator'),
            (SimTrading, 'simulator_trading'),
            (SimulatorConfig, 'simulator_config'),
            (AgentTrading, 'agent_trading'),
        ]

        total_records = 0
        # 导出每个表
        for table_class, table_name in tables:
            count = export_table_to_json(db.session, table_class, table_name, output_dir)
            total_records += count

        # 创建元数据文件
        metadata = {
            'export_time': datetime.now().isoformat(),
            'database': db_config['database'],
            'total_tables': len(tables),
            'total_records': total_records,
            'tables': [
                {'name': name, 'model': model.__name__}
                for model, name in tables
            ]
        }

        metadata_file = os.path.join(output_dir, '_metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"\n✅ JSON 导出成功! 共 {len(tables)} 个表, {total_records} 条记录")
        print(f"📁 输出目录: {output_dir}")
        return True

    except Exception as e:
        print(f"❌ JSON 导出失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='数据库导出脚本')
    parser.add_argument('--sql-only', action='store_true', help='仅导出 SQL 文件')
    parser.add_argument('--json-only', action='store_true', help='仅导出 JSON 文件')
    parser.add_argument('--output-dir', type=str, default='./backups', help='输出目录')
    parser.add_argument('--config', type=str, default='../../service.conf', help='配置文件路径')

    args = parser.parse_args()

    # 获取数据库配置
    db_config = get_db_config(args.config)

    # 创建输出目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(args.output_dir, f"backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"🗄️  数据库导出工具")
    print(f"{'='*60}")
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔌 后端: {db_config['backend']}")
    print(f"🗃️  数据库: {db_config['database']}")
    if db_config['backend'] == 'sqlite':
        print(f"📍 SQLite: {db_config['sqlite_path']}")
    else:
        print(f"🌐 MySQL: {db_config['host']}:{db_config['port']}")
    print(f"{'='*60}\n")

    success = True

    # 导出 SQL
    if not args.json_only:
        sql_file = os.path.join(backup_dir, f"{db_config['database']}_{timestamp}.sql")
        if not export_to_sql(db_config, sql_file):
            success = False

    # 导出 JSON
    if not args.sql_only:
        json_dir = os.path.join(backup_dir, 'json_export')
        if not export_to_json(db_config, json_dir):
            success = False

    print(f"\n{'='*60}")
    if success:
        print(f"✅ 导出完成! 备份位置: {backup_dir}")
    else:
        print(f"⚠️  导出完成，但部分操作可能失败")
    print(f"{'='*60}\n")

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
