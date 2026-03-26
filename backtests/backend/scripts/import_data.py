#!/usr/bin/env python
"""
从 JSON 文件导入配置数据到新数据库
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from end_points.init_global import init_global
from end_points.config.global_var import global_var
from db.models import Rule, SimulatorConfig

def import_data():
    """从 JSON 导入配置数据"""
    try:
        # 读取导出的数据
        data_file = os.path.join(os.path.dirname(__file__), 'data_export.json')
        if not os.path.exists(data_file):
            print(f"❌ 数据文件不存在: {data_file}")
            print("   请先运行 export_data.py 导出数据")
            return False
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 初始化数据库连接
        config_file = os.path.join(os.path.dirname(__file__), '..', 'service.conf')
        init_global(config_file)
        db = global_var['db']
        
        # 1. 导入 Rule 表
        if 'rules' in data:
            print(f"导入 Rule 表 ({len(data['rules'])} 条)...")
            for rule_data in data['rules']:
                # 检查是否已存在
                existing = db.session.query(Rule).filter(Rule.id == rule_data['id']).first()
                if existing:
                    # 更新
                    existing.name = rule_data['name']
                    existing.type = rule_data['type']
                    existing.info = rule_data['info']
                    if rule_data.get('description'):
                        existing.description = rule_data['description']
                    if 'agent_id' in rule_data:
                        existing.agent_id = rule_data.get('agent_id')
                    print(f"  更新 Rule {rule_data['id']}: {rule_data['name']}")
                else:
                    # 插入新记录
                    new_rule = Rule(
                        id=rule_data['id'],
                        name=rule_data['name'],
                        type=rule_data['type'],
                        info=rule_data['info'],
                        description=rule_data.get('description'),
                        agent_id=rule_data.get('agent_id'),
                    )
                    db.session.add(new_rule)
                    print(f"  插入 Rule {rule_data['id']}: {rule_data['name']}")
            
            db.session.commit()
            print("  ✅ Rule 表导入完成")
        
        # 2. 导入 SimulatorConfig 表
        if 'simulator_config' in data:
            print("导入 SimulatorConfig 表...")
            config_data = data['simulator_config']
            
            # 检查是否已存在
            existing = db.session.query(SimulatorConfig).filter(SimulatorConfig.id == config_data['id']).first()
            if existing:
                existing.profit_threshold = config_data['profit_threshold']
                existing.stop_loss = config_data['stop_loss']
                existing.max_holding_days = config_data['max_holding_days']
                print(f"  更新配置: profit={config_data['profit_threshold']}%, stop_loss={config_data['stop_loss']}%, days={config_data['max_holding_days']}")
            else:
                new_config = SimulatorConfig(
                    id=config_data['id'],
                    profit_threshold=config_data['profit_threshold'],
                    stop_loss=config_data['stop_loss'],
                    max_holding_days=config_data['max_holding_days']
                )
                db.session.add(new_config)
                print(f"  插入配置: profit={config_data['profit_threshold']}%, stop_loss={config_data['stop_loss']}%, days={config_data['max_holding_days']}")
            
            db.session.commit()
            print("  ✅ SimulatorConfig 导入完成")
        
        print("\n✅ 数据导入完成!")
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_data()
    sys.exit(0 if success else 1)
