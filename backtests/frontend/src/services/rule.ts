import { get, post, put, del } from '@/utils/request'
import * as urls from './urls'
import type { Rule, PageParams } from '@/types'

export const ruleService = {
  getRuleList: (params: PageParams = {}) => {
    return get(urls.getRuleListUrl(params))
  },

  getRule: (id: number, params: any = {}) => {
    return get(urls.getRuleUrl(id, params))
  },

  getRuleStocks: (id: number, params: any = {}) => {
    return get(urls.getRuleStockListUrl(id, params))
  },

  getRulePools: (id: number, params: any = {}) => {
    return get(urls.getRulePoolUrl(id, params))
  },

  getRuleParams: (id: number, params: any = {}) => {
    return get(urls.getRuleParamListUrl(id, params))
  },

  addPoolsToRule: (id: number, data: { pool_ids: number[] }) => {
    return post(urls.getRulePoolUrl(id), data)
  },

  deletePoolFromRule: (id: number, data: { pool_id: number }) => {
    return del(urls.getRulePoolUrl(id), data)
  },

  addRule: (data: Partial<Rule>) => {
    return post(urls.getRuleListUrl({}), data)
  },

  updateRule: (id: number, data: Partial<Rule>) => {
    return put(urls.getRuleUrl(id), data)
  },

  deleteRule: (id: number) => {
    return del(urls.getRuleUrl(id))
  },
}
