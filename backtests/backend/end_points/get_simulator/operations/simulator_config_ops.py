import logging
from db.models import SimulatorConfig


def get_simulator_config(db):
    """Get global simulator configuration (id=1)"""
    try:
        config = db.session.query(SimulatorConfig).filter(SimulatorConfig.id == 1).first()
        if not config:
            # Create default config if not exists
            config = SimulatorConfig(
                id=1,
                profit_threshold=0,
                stop_loss=5,
                max_holding_days=5
            )
            db.session.add(config)
            db.session.commit()
        
        return {
            'code': 'SUCCESS',
            'data': {
                'id': config.id,
                'profit_threshold': config.profit_threshold,
                'stop_loss': config.stop_loss,
                'max_holding_days': config.max_holding_days,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None
            }
        }
    except Exception as e:
        logging.error(f"Error in get_simulator_config: {e}")
        db.session.rollback()
        return {
            'code': 'FAILURE',
            'message': str(e)
        }


def update_simulator_config(db, profit_threshold, stop_loss, max_holding_days):
    """Update global simulator configuration (id=1)"""
    try:
        config = db.session.query(SimulatorConfig).filter(SimulatorConfig.id == 1).first()
        if not config:
            # Create default config if not exists
            config = SimulatorConfig(id=1)
        
        config.profit_threshold = profit_threshold
        config.stop_loss = stop_loss
        config.max_holding_days = max_holding_days
        
        db.session.add(config)
        db.session.commit()
        
        return {
            'code': 'SUCCESS',
            'data': {
                'id': config.id,
                'profit_threshold': config.profit_threshold,
                'stop_loss': config.stop_loss,
                'max_holding_days': config.max_holding_days,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None
            }
        }
    except Exception as e:
        logging.error(f"Error in update_simulator_config: {e}")
        db.session.rollback()
        return {
            'code': 'FAILURE',
            'message': str(e)
        }
