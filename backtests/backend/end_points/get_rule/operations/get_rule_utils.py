from db.models import Pool, RulePool, Rule


def getPoolsForRule(db, rule_id):
    pools = db.session.query(Pool) \
        .join(RulePool, RulePool.pool_id == Pool.id) \
        .filter(RulePool.rule_id == rule_id).all()
    return pools

def getPoolNamesForRule(db, rule_id):
    pools = db.session.query(Pool.name) \
        .join(RulePool, RulePool.pool_id == Pool.id) \
        .filter(RulePool.rule_id == rule_id).order_by(Pool.id).all()
    pool_names = ""
    for each in pools:
        pool_names += each[0] + " "
    return pool_names.strip()

def cleanStockRuleEarnForStock(db, model_class, stock_code):
    stock_rule_records = db.session.query(model_class) \
        .filter(model_class.stock_code == stock_code).all()
    if stock_rule_records:
        for i in stock_rule_records:
            db.session.delete(i)
        db.session.commit()
    return

def cleanStockRuleEarnForRule(db, model_class, rule_id):
    stock_rule_earn_records = db.session.query(model_class) \
        .filter(model_class.rule_id == rule_id).all()
    if stock_rule_earn_records:
        for record in stock_rule_earn_records:
            db.session.delete(record)
        db.session.commit()
    return

def cleanPoolRuleEarnForRulePool(db, model_class, rule_id, pool_id):
    pool_rule_records = db.session.query(model_class) \
        .filter(model_class.rule_id == rule_id) \
        .filter(model_class.pool_id == pool_id).all()
    if pool_rule_records:
        for i in pool_rule_records:
            db.session.delete(i)
        db.session.commit()
    return

def cleanPoolRuleEarnForRule(db, model_class, rule_id):
    pool_rule_records = db.session.query(model_class) \
        .filter(model_class.rule_id == rule_id).all()
    if pool_rule_records:
        for i in pool_rule_records:
            db.session.delete(i)
        db.session.commit()
    return

def cleanPoolRuleEarnForPool(db, model_class, pool_id):
    pool_rule_earn_records = db.session.query(model_class) \
        .filter(model_class.pool_id == pool_id).all()
    if pool_rule_earn_records:
        for i in pool_rule_earn_records:
            db.session.delete(i)
        db.session.commit()
    return
