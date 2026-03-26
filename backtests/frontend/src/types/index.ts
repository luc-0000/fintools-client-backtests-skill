// 基础响应类型
export type BaseResponseType<T = any> = {
  code: string | number
  data: T
  errMsg?: string
}

// 日期时间类型
export type DateTime = string

// Pool 类型
export type Pool = {
  id: number
  name: string
  stocks?: number
  latest_date?: DateTime
  earn?: number
  avg_earn?: number
  earning_rate?: number
  trading_times?: number
  updated_at?: DateTime
}

// Stock 类型
export type Stock = {
  code: string
  name: string
  earn?: number
  avg_earn?: number
  earning_rate?: number
  trading_times?: number
  cap?: number
  earn_updated_at: DateTime
  updated_at?: DateTime
}

// StockDetails 类型
export type StockDetails = {
  date: string
  volume: number
  turnover: number
  turnover_rate: number
  open: number
  close: number
  high: number
  low: number
  shake_rate: number
  chane_rate: number
  change_amount: number
  k: number
  d: number
  j: number
  diff: number
  dea: number
  macd: number
  ema12: number
  ema26: number
  ma3: number
  ma5: number
  ma10: number
  ma15: number
  ma20: number
  ma30: number
  ma60: number
  ma120: number
  ma200: number
  ma250: number
  boll_u: number
  boll_d: number
  boll_m: number
}

// Rule 类型
export type Rule = {
  id: number
  name: string
  type: string
  split?: number
  description: string
  pools: string
  stocks?: number
  func?: string
  earn?: number
  avg_earn?: number
  earning_rate?: number
  trading_times?: number
  threshould?: number
  t0_earn?: number
  t0_earn_rate?: number
  t0_trading?: number
  max_earn?: number
  max_ce_er?: number
  max_earn_rate?: number
  info?: string
  agent_id?: string
  model_location?: string
  scaler_location?: string
  encoder_location?: string
  updated_at?: DateTime
}

// EarnData 类型
export type EarnData = {
  indicating_date: string
  indicating_price: number
  buy_date: string
  buy_price: number
  sell_date: string
  sell_price: number
  earn: number
  dates_diff: number
  amount: number
}

// StockRuleEarn 类型
export type StockRuleEarn = {
  id?: number
  code?: string
  name?: string
  stock_code?: string
  stock_name?: string
  rule_id: number
  rule_name?: string
  earn?: number
  avg_earn?: number
  earning_rate?: number
  trading_times?: number
  status?: string
  indicating_date?: DateTime
  updated_at?: DateTime
  earn_updated_at?: DateTime
  cap?: number
}

// Simulator 类型
export type Simulator = {
  id?: number
  stock_code?: string
  stock_name?: string
  rule_id?: number
  rule_name?: string
  status?: string
  init_money?: number
  current_money?: number
  current_share?: number
  current_shares?: string
  cum_earn?: number
  avg_earn?: number
  earning_rate?: number
  trading_times?: number
  r_cum_earn_after?: number
  r_earn_rate_after?: number
  r_avg_earn_after?: number
  r_trading_times?: number
  max_drawback?: number
  sharpe?: number
  start_date?: DateTime
  first_trade_date?: DateTime
  annual_earn?: number
  indicating_date?: DateTime
  updated_at?: DateTime
}

// SimTrading 类型
export type SimTrading = {
  id: number
  sim_id: number
  stock?: string
  trading_type?: string
  trading_date?: DateTime
  trading_amount?: number
  updated_at?: DateTime
}

// Tradings 类型
export type Tradings = {
  id?: number
  rule_id?: number
  sims?: number
  rule_name?: string
  stock?: string
  stock_name?: string
  trading_date?: DateTime
  type?: string
  init_money?: number
  price?: number
  share?: number
  sold?: boolean
  created_at?: DateTime
  updated_at?: DateTime
}

// TradeEarn 类型
export type TradeEarn = {
  id?: number
  rule_id?: number
  sim_id?: number
  cum_earn?: number
  trading_times?: number
  created_at?: DateTime
  updated_at?: DateTime
}

// RuleTrading 类型
export type RuleTrading = {
  id: number
  rule_id: number
  stock?: string
  trading_date: DateTime
  trading_type?: string
  trading_amount?: number
  created_at?: DateTime
  updated_at?: DateTime
}

// 分页参数
export type PageParams = {
  current?: number
  pageSize?: number
  [key: string]: any
}

// 分页响应
export type PageResponse<T> = {
  data: T[]
  total: number
  success: boolean
}
