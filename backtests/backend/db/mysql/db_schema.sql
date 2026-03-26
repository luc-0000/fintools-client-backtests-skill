-- ============================================
-- fintools_backtest 数据库架构
-- Agent 系统精简版
-- ============================================

CREATE TABLE IF NOT EXISTS `stock` (
    `code`       varchar(64)    NOT NULL COMMENT '代码',
    `name`       varchar(64)    NOT NULL COMMENT '名称',
    `se`         varchar(64)    NOT NULL COMMENT '交易所',
    `type`       varchar(64)    DEFAULT NULL COMMENT '类型',
    `index_code` varchar(64)    DEFAULT NULL COMMENT '指数代码',
    `created_at` datetime       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` datetime       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`code`) USING BTREE,
    KEY `idx_se` (`se`),
    KEY `idx_type` (`type`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT='股票基本信息';

CREATE TABLE IF NOT EXISTS `pool`
(
    `id`            int(11)         NOT NULL AUTO_INCREMENT COMMENT '主key',
    `name`          varchar(32)     NOT NULL COMMENT '名称',
    `stocks`        int(11)         NOT NULL DEFAULT 0 COMMENT '股票数量',
    `latest_date`   datetime        DEFAULT NULL COMMENT '最新日期',
    `created_at`    datetime        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`    datetime        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE,
    KEY `idx_name` (`name`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT='股票池';

CREATE TABLE IF NOT EXISTS `pool_stock`
(
    `id`          int(11)      NOT NULL AUTO_INCREMENT COMMENT '主key',
    `stock_code`  varchar(32)  NOT NULL COMMENT '股票代码',
    `pool_id`     int(11)      NOT NULL COMMENT '股票池ID',
    `created_at`  datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`  datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE,
    KEY `idx_stock_code` (`stock_code`),
    KEY `idx_pool_id` (`pool_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT='股票池股票关联';

CREATE TABLE IF NOT EXISTS `rule`
(
    `id`          int(11)          NOT NULL COMMENT '规则ID',
    `name`        varchar(255)     NOT NULL COMMENT '名称',
    `type`        varchar(255)     NOT NULL COMMENT '类型',
    `info`        text             NOT NULL COMMENT '规则信息(JSON)',
    `description` varchar(255)     DEFAULT '' COMMENT '描述',
    `created_at`  datetime         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`  datetime         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE,
    KEY `idx_type` (`type`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT='交易规则';

CREATE TABLE IF NOT EXISTS `rule_pool`
(
    `id`       int(11)     NOT NULL AUTO_INCREMENT COMMENT '主key',
    `rule_id`  int(11)     NOT NULL COMMENT '规则ID',
    `pool_id`  int(11)     NOT NULL COMMENT '股票池ID',
    `created_at` datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE,
    KEY `idx_rule_id` (`rule_id`),
    KEY `idx_pool_id` (`pool_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT='规则股票池关联';

CREATE TABLE IF NOT EXISTS `stock_rule_earn`
(
    `id`              int(11)      NOT NULL AUTO_INCREMENT COMMENT '主key',
    `stock_code`      varchar(64)  NOT NULL COMMENT '股票代码',
    `rule_id`         int(11)      NOT NULL COMMENT '规则ID',
    `earn`            float(11,2)  DEFAULT NULL COMMENT '累计收益',
    `avg_earn`        float(11,2)  DEFAULT NULL COMMENT '平均收益',
    `earning_rate`    float(11,2)  DEFAULT NULL COMMENT '盈利率',
    `trading_times`   int(11)      DEFAULT NULL COMMENT '交易次数',
    `status`          varchar(32)  DEFAULT 'normal' COMMENT '状态',
    `indicating_date` datetime     DEFAULT NULL COMMENT '信号日期',
    `updated_at`      datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE,
    KEY `idx_stock_code` (`stock_code`),
    KEY `idx_rule_id` (`rule_id`),
    KEY `idx_status` (`status`),
    KEY `idx_indicating_date` (`indicating_date`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT='股票规则收益（核心预计算信号）';

CREATE TABLE IF NOT EXISTS `pool_rule_earn`
(
    `id`             int(11)      NOT NULL AUTO_INCREMENT COMMENT '主key',
    `pool_id`        int(11)      NOT NULL COMMENT '股票池ID',
    `rule_id`        int(11)      NOT NULL COMMENT '规则ID',
    `earn`           float(11,2)  DEFAULT NULL COMMENT '累计收益',
    `avg_earn`       float(11,2)  DEFAULT NULL COMMENT '平均收益',
    `earning_rate`   float(11,2)  DEFAULT NULL COMMENT '盈利率',
    `trading_times`  int(11)      DEFAULT NULL COMMENT '交易次数',
    `updated_at`     datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE,
    KEY `idx_pool_id` (`pool_id`),
    KEY `idx_rule_id` (`rule_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT='股票池规则收益';

CREATE TABLE IF NOT EXISTS `simulator`
(
    `id`               int(11)          NOT NULL AUTO_INCREMENT COMMENT '主key',
    `stock_code`       varchar(32)      DEFAULT NULL COMMENT '股票代码',
    `rule_id`          int(11)          NOT NULL COMMENT '规则ID',
    `start_date`       datetime         DEFAULT NULL COMMENT '开始日期',
    `status`           varchar(32)      NOT NULL DEFAULT 'running' COMMENT '状态',
    `init_money`       float            DEFAULT 10000 COMMENT '初始资金',
    `current_money`    float            DEFAULT 10000 COMMENT '当前资金',
    `current_shares`   text             DEFAULT 0 COMMENT '当前持仓',
    `cum_earn`         float(11,2)      DEFAULT NULL COMMENT '累计收益',
    `avg_earn`         float(11,2)      DEFAULT NULL COMMENT '平均收益',
    `earning_rate`     float(11,2)      DEFAULT NULL COMMENT '盈利率',
    `trading_times`    int(11)          DEFAULT NULL COMMENT '交易次数',
    `indicating_date`  datetime         DEFAULT NULL COMMENT '信号日期',
    `earning_info`     text             DEFAULT NULL COMMENT '收益信息',
    `created_at`       datetime         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`       datetime         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE,
    KEY `idx_rule_id` (`rule_id`),
    KEY `idx_status` (`status`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT='模拟器';

CREATE TABLE IF NOT EXISTS `simulator_trading`
(
    `id`             int(11)     NOT NULL AUTO_INCREMENT COMMENT '主key',
    `sim_id`         int(11)     NOT NULL COMMENT '模拟器ID',
    `stock`          varchar(64) NOT NULL DEFAULT 'stock' COMMENT '股票代码',
    `trading_date`   datetime    NOT NULL COMMENT '交易日期',
    `trading_type`   varchar(64) NOT NULL DEFAULT 'buy' COMMENT '交易类型',
    `trading_amount` float       NOT NULL DEFAULT 0 COMMENT '交易金额',
    `created_at`     datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`     datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE,
    KEY `idx_sim_id` (`sim_id`),
    KEY `idx_trading_date` (`trading_date`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT='模拟器交易记录';

CREATE TABLE IF NOT EXISTS `model_rule_return`
(
    `rule_id`        int(11)          NOT NULL COMMENT '规则ID',
    `earn`           float(11,2)      DEFAULT NULL COMMENT '累计收益',
    `avg_earn`       float(11,2)      DEFAULT NULL COMMENT '平均收益',
    `earning_rate`   float(11,2)      DEFAULT NULL COMMENT '盈利率',
    `trading_times`  int(11)          DEFAULT NULL COMMENT '交易次数',
    `avg_earns_thres` text             DEFAULT NULL COMMENT '阈值收益',
    `data_type`      varchar(64)      DEFAULT NULL COMMENT '数据类型',
    `trained_at`     datetime         DEFAULT NULL COMMENT '训练时间',
    `updated_at`     datetime         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`rule_id`) USING BTREE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT='DL模型规则收益（历史数据）';

CREATE TABLE IF NOT EXISTS `rule_trading`
(
    `id`             int(11)     NOT NULL AUTO_INCREMENT COMMENT "主key",
    `rule_id`        int(11)     NOT NULL COMMENT "规则ID",
    `stock`          varchar(64) NOT NULL DEFAULT "stock" COMMENT "股票代码",
    `trading_date`   datetime    NOT NULL COMMENT "交易日期",
    `trading_type`   varchar(64) NOT NULL DEFAULT "buy" COMMENT "交易类型",
    `trading_amount` float       NOT NULL DEFAULT 0 COMMENT "交易金额",
    `created_at`     datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间",
    `updated_at`     datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "更新时间",
    PRIMARY KEY (`id`) USING BTREE,
    KEY `idx_rule_id` (`rule_id`),
    KEY `idx_trading_date` (`trading_date`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  ROW_FORMAT = DYNAMIC
  COMMENT="规则交易记录";
