import { buildUrlWithTs } from '@/utils/utils'

// 所有路径都返回相对路径，通过 Vite proxy 转发到后端

// pool
export function getPoolListUrl(params: any = {}) {
  return buildUrlWithTs(`/v1/get_pool/pool_list`, params)
}

export function getPoolUrl(id: number) {
  return buildUrlWithTs(`/v1/get_pool/pool/${id}`, {})
}

// stock list (for pools)
export function getStockListUrl(params: any = {}) {
  return buildUrlWithTs(`/v1/get_stock/stock_list`, params)
}

// rule
export function getRuleListUrl(params: any = {}) {
  return buildUrlWithTs(`/v1/get_rule/rule_list`, params)
}

export function getRuleUrl(id: number, params: any = {}) {
  return buildUrlWithTs(`/v1/get_rule/rule/${id}`, params)
}

export function getRulePoolUrl(id: number, params: any = {}) {
  return buildUrlWithTs(`/v1/get_rule/rule/${id}/pools`, params)
}

export function getRuleStockListUrl(id: number, params: any = {}) {
  return buildUrlWithTs(`/v1/get_rule/rule/${id}/stocks`, params)
}

export function getRuleParamListUrl(id: number, params: any = {}) {
  return buildUrlWithTs(`/v1/get_rule/rule/${id}/params`, params)
}

// simulator
export function getSimulatorListUrl(params: any = {}) {
  return buildUrlWithTs(`/v1/get_simulator/simulator_list`, params)
}

export function getSimulatorUrl(id: number) {
  return buildUrlWithTs(`/v1/get_simulator/simulator/${id}`, {})
}

export function getSimParamsUrl(id: number, params: any = {}) {
  return buildUrlWithTs(`/v1/get_simulator/simulator/${id}/params`, params)
}

export function getSimTradingUrl(id: number, params: any = {}) {
  return buildUrlWithTs(`/v1/get_simulator/simulator/${id}/trading`, params)
}

export function getTradingsUrl(params: any = {}) {
  return buildUrlWithTs(`/v1/get_simulator/trading_list`, params)
}

export function getTradeEarnsUrl(params: any = {}) {
  return buildUrlWithTs(`/v1/get_simulator/earn_list`, params)
}

// rule agent operations
export function getRuleRunUrl(id: number) {
  return buildUrlWithTs(`/v1/get_rule/rule/run/${id}`, {})
}

export function getRuleTradingUrl(id: number, params: any = {}) {
  return buildUrlWithTs(`/v1/get_rule/rule/${id}/trading`, params)
}

export function getRuleStocksIndicatingUrl(id: number) {
  return buildUrlWithTs(`/v1/get_rule/rule/${id}/stocks_indicating`, {})
}

export function getRuleRunStockUrl(id: number, stockCode: string) {
  return buildUrlWithTs(`/v1/get_rule/rule/${id}/run_stock`, { stock_code: stockCode })
}
