import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { Stock } from '@/types'
import { stockService } from '@/services'

export const usePoolStockListModel = (poolId: number) => {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const fetchStocks = useCallback(async (params: any = {}) => {
    setLoading(true)
    try {
      const response = await stockService.getStockList({ pool_id: poolId, ...params })
      if (response && response.data && response.data.items) {
        setStocks(response.data.items)
        setTotal(response.data.total)
      } else if (Array.isArray(response)) {
        setStocks(response)
        setTotal(response.length)
      } else {
        setStocks([])
        setTotal(0)
      }
    } catch (error) {
      message.error('获取股票列表失败')
      console.error('Failed to fetch stocks:', error)
    } finally {
      setLoading(false)
    }
  }, [poolId])

  useEffect(() => {
    if (poolId) {
      fetchStocks({ pool_id: poolId })
    }
  }, [poolId])

  return { stocks, total, loading, fetchStocks }
}

export const useAllStocksListModel = () => {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(false)

  const fetchAllStocks = useCallback(async () => {
    setLoading(true)
    try {
      const response = await stockService.getStockList({})
      if (response && response.data && response.data.items) {
        setStocks(response.data.items)
      }
    } catch (error) {
      message.error('Failed to fetch all stocks')
      console.error('Failed to fetch all stocks:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  return { stocks, loading, fetchAllStocks }
}

export const usePoolStockMutations = (poolId: number) => {
  const addStockToPool = useCallback(async (stockCode: string) => {
    try {
      await stockService.addStock({ code: stockCode, pool_id: poolId })
      message.success('添加成功')
      return { success: true }
    } catch (error) {
      message.error('添加失败')
      return { success: false, error }
    }
  }, [poolId])

  const deleteStockFromPool = useCallback(async (stockCode: string) => {
    try {
      await stockService.deleteStock(stockCode, { pool_id: poolId })
      message.success('删除成功')
      return { success: true }
    } catch (error) {
      message.error('删除失败')
      return { success: false, error }
    }
  }, [poolId])

  return { addStockToPool, deleteStockFromPool }
}
