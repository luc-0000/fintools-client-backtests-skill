from db.models import Pool, PoolStock, RulePool, Stock


def update_latest_date(db):
    all_pools = db.session.query(Pool).order_by(Pool.id).all()
    for each_pool in all_pools:
        pool_id = each_pool.id
        query = db.session.query(Stock.updated_at).join(PoolStock, PoolStock.stock_code == Stock.code).filter(PoolStock.pool_id == pool_id)
        rows = query.all()
        dates = [x for (x,) in rows]
        latest_date = min(dates) if len(dates) > 0 else None
        each_pool.latest_date = latest_date
    db.session.commit()
