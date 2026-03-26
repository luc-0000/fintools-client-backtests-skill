import { post, get } from '@/utils/request'
import * as urls from './urls'
import type { PageParams } from '@/types'

// Rule Agent 服务（运行 agent 类型的 rule）
export const agentService = {
  // 开始执行 Rule (所有stocks)
  startRuleExecution: (rule_id: number) => {
    return post(`/v1/get_rule/rule/${rule_id}/start`, {})
  },

  // 开始执行单个 stock
  startStockExecution: (rule_id: number, stock_code: string) => {
    return post(`/v1/get_rule/rule/${rule_id}/stock/${stock_code}/start`, {})
  },

  // 运行 Rule Agent (30 minutes timeout for long-running tasks)
  runAgent: (rule_id: number, payload: any = {}) => {
    return post(urls.getRuleRunUrl(rule_id), payload, { timeout: 1800000 }) // 30 minutes
  },

  // 获取 Rule Trading 列表
  getRuleTrading: (rule_id: number, params: PageParams = {}) => {
    return get(urls.getRuleTradingUrl(rule_id, params))
  },

  // 获取 Rule Stocks Indicating 状态
  getRuleStocksIndicating: (rule_id: number) => {
    return get(urls.getRuleStocksIndicatingUrl(rule_id))
  },

  // 运行单个stock的agent (30 minutes timeout for long-running tasks)
  runAgentForStock: (rule_id: number, stock_code: string) => {
    return post(urls.getRuleRunStockUrl(rule_id, stock_code), {}, { timeout: 1800000 })
  },
}

export default agentService
