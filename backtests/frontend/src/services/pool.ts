import { get, post, put, del } from '@/utils/request'
import * as urls from './urls'
import type { Pool, PageParams } from '@/types'

export const poolService = {
  getPoolList: (params: PageParams = {}) => {
    return get(urls.getPoolListUrl(params))
  },

  getPool: (id: number) => {
    return get(urls.getPoolUrl(id))
  },

  addPool: (data: Partial<Pool>) => {
    return post(urls.getPoolListUrl({}), data)
  },

  updatePool: (id: number, data: Partial<Pool>) => {
    return put(urls.getPoolUrl(id), data)
  },

  deletePool: (id: number) => {
    return del(urls.getPoolUrl(id))
  },
}
