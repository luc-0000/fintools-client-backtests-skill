import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { Pool, StockRuleEarn, RuleTrading } from '@/types'
import { ruleService, agentService } from '@/services'

export const useRulePoolListModel = (ruleId: number, bindKey: string = 'cn_stocks') => {
  const [pools, setPools] = useState<Pool[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const fetchPools = useCallback(async () => {
    setLoading(true)
    try {
      const response = await ruleService.getRulePools(ruleId, { bind_key: bindKey })
      if (response && response.data && response.data.items) {
        setPools(response.data.items)
        setTotal(response.data.total)
      } else {
        setPools([])
        setTotal(0)
      }
    } catch (error) {
      message.error('Failed to fetch rule pools')
      console.error('Failed to fetch rule pools:', error)
    } finally {
      setLoading(false)
    }
  }, [ruleId, bindKey])

  const addPoolToRuleFunc = useCallback(async (poolIds: number[]) => {
    try {
      await ruleService.addPoolsToRule(ruleId, { pool_ids: poolIds })
      message.success('添加成功')
      await fetchPools()
    } catch (error) {
      message.error('添加失败')
      throw error
    }
  }, [ruleId, fetchPools])

  const deletePoolFromRuleFunc = useCallback(async (poolId: number) => {
    try {
      await ruleService.deletePoolFromRule(ruleId, { pool_id: poolId })
      message.success('删除成功')
      await fetchPools()
    } catch (error) {
      message.error('删除失败')
      throw error
    }
  }, [ruleId, fetchPools])

  useEffect(() => {
    if (ruleId) {
      fetchPools()
    }
  }, [ruleId, bindKey])

  return { pools, total, loading, fetchPools, addPoolToRuleFunc, deletePoolFromRuleFunc }
}

export const useRuleStockListModel = (ruleId: number, bindKey: string = 'cn_stocks', poolId?: number) => {
  const [stocks, setStocks] = useState<StockRuleEarn[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const fetchStocks = useCallback(async (poolId?: number) => {
    setLoading(true)
    try {
      const params: any = { bind_key: bindKey }
      if (poolId) {
        params.pool_id = poolId
      }
      const response = await ruleService.getRuleStocks(ruleId, params)
      if (response && response.data && response.data.items) {
        setStocks(response.data.items)
        setTotal(response.data.total)
      } else {
        setStocks([])
        setTotal(0)
      }
    } catch (error) {
      message.error('Failed to fetch rule stocks')
      console.error('Failed to fetch rule stocks:', error)
    } finally {
      setLoading(false)
    }
  }, [ruleId, bindKey])

  useEffect(() => {
    if (ruleId) {
      fetchStocks(poolId)
    }
  }, [ruleId, bindKey, poolId])

  return { stocks, total, loading, fetchStocks }
}

export const useAllPoolsListModel = () => {
  const [pools, setPools] = useState<Pool[]>([])
  const [loading, setLoading] = useState(false)

  const fetchAllPools = useCallback(async () => {
    setLoading(true)
    try {
      const { poolService } = await import('@/services')
      const response = await poolService.getPoolList({})
      if (response && response.data && response.data.items) {
        setPools(response.data.items)
      }
    } catch (error) {
      message.error('Failed to fetch all pools')
      console.error('Failed to fetch all pools:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  return { pools, loading, fetchAllPools }
}

export const useRuleTradingListModel = (ruleId: number, page: number = 1, pageSize: number = 50) => {
  const [tradings, setTradings] = useState<RuleTrading[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const fetchTradings = useCallback(async (pageNum: number = page, pageSizeNum: number = pageSize) => {
    setLoading(true)
    try {
      const response = await agentService.getRuleTrading(ruleId, { page: pageNum, page_size: pageSizeNum })
      if (response && response.data && response.data.items) {
        setTradings(response.data.items)
        setTotal(response.data.total)
      } else {
        setTradings([])
        setTotal(0)
      }
    } catch (error) {
      message.error('Failed to fetch rule tradings')
      console.error('Failed to fetch rule tradings:', error)
    } finally {
      setLoading(false)
    }
  }, [ruleId, page, pageSize])

  useEffect(() => {
    if (ruleId) {
      fetchTradings()
    }
  }, [ruleId])

  return { tradings, total, loading, fetchTradings }
}
