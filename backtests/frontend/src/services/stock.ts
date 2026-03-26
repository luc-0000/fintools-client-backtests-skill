import { get, post, del } from '@/utils/request'
import * as urls from './urls'
import type { Stock, PageParams } from '@/types'

export const stockService = {
  getStockList: (params: PageParams = {}) => {
    return get(urls.getStockListUrl(params))
  },

  addStock: (data: Partial<Stock> & { pool_id?: number }) => {
    return post(urls.getStockListUrl({}), data)
  },

  deleteStock: (code: string, params?: PageParams) => {
    return del(`/v1/get_stock/stock/${code}`, params)
  },
}
