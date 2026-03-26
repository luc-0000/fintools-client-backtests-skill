// Constants definition
export const MinRate = -100
export const MinDate = '1900-1-1T00:00:00'

export const DatabaseNames = {
  CNStocks: "cn_stocks",
  CNStocksDH: "cn_stocks_dh",
  CNStocksDQ: "cn_stocks_dq",
  AIStock: "ai_stock"
}

export const RuleNames = {
  NORule: "no",
  JDK: "jdk",
  MACD: "macd",
  BOLL: "boll"
}

export const SimStatus = {
  Created: "created",
  Running: "running",
  Stopped: "stopped",
  Indicating: "indicating",
  Holding: "holding",
  Normal: "normal"
}

export const RuleType = {
  mclose: "mclose",
  mopen: "mopen",
  tech: "tech",
  rl: "rl",
  combo: "combo",
  agent: "agent"
}

export const TradingTypes = {
  buy: "buy",
  sell: "sell",
  fail_to_buy: "fail_to_buy",
  fail_to_sell: "fail_to_sell",
}
