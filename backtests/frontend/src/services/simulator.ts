import { get, post, put, del } from '@/utils/request'
import * as urls from './urls'
import type { Simulator, PageParams } from '@/types'

export const simulatorService = {
  getSimulatorList: (params: PageParams = {}) => {
    return get(urls.getSimulatorListUrl(params))
  },

  getSimulator: (id: number) => {
    return get(urls.getSimulatorUrl(id))
  },

  getSimulatorParams: (id: number, params: any = {}) => {
    return get(urls.getSimParamsUrl(id, params))
  },

  getSimulatorTrading: (id: number, params: any = {}) => {
    return get(urls.getSimTradingUrl(id, params))
  },

  addSimulator: (data: Partial<Simulator>) => {
    return post(urls.getSimulatorListUrl({}), data)
  },

  updateSimulator: (id: number, data?: any) => {
    return put(urls.getSimulatorUrl(id), data)
  },

  deleteSimulator: (id: number) => {
    return del(urls.getSimulatorUrl(id))
  },

  runSimulator: (id: number) => {
    return put(`/v1/get_simulator/simulator/${id}/run`, {}, { timeout: 600000 }) // 10 minutes
  },

  getTradings: (params: PageParams = {}) => {
    return get(urls.getTradingsUrl(params))
  },

  getTradeEarns: (params: PageParams = {}) => {
    return get(urls.getTradeEarnsUrl(params))
  },
}
