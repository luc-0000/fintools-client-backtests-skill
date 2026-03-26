import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { Stock, PageParams, BaseResponseType } from '@/types'
import { stockService } from '@/services'

type StateType = {
  stocks: Stock[]
  total: number
  loading: boolean
}

export type StockListParams = {
  current?: number
  pageSize?: number
  pool_id?: number
}

export const useStockListModel = (params: StockListParams = {}) => {
  const initState: StateType = { stocks: [], total: 0, loading: true }
  const [state, setState] = useState<StateType>(initState)

  const fetchData = useCallback(async (params: StockListParams) => {
    setState({ ...state, loading: true })
    try {
      const response = await stockService.getStockList(params) as BaseResponseType<{ items: Stock[], total: number }>
      if (response.code === 'SUCCESS') {
        setState({
          stocks: response.data.items || [],
          total: response.data.total || 0,
          loading: false
        })
      } else if (Array.isArray(response)) {
        setState({ stocks: response, total: response.length, loading: false })
      } else {
        setState({ stocks: [], total: 0, loading: false })
      }
    } catch (error) {
      message.error('Failed to fetch stocks')
      console.error('Failed to fetch stocks:', error)
      setState({ ...initState, loading: false })
    }
  }, [])

  const addStockFunc = useCallback(async (stock: Partial<Stock>) => {
    try {
      await stockService.addStock(stock)
      message.success('Stock added successfully')
      await fetchData(params)
    } catch (error) {
      message.error('Failed to add stock')
      console.error('Failed to add stock:', error)
      throw error
    }
  }, [params])

  const deleteStockFunc = useCallback(async (code: string, params?: PageParams) => {
    try {
      await stockService.deleteStock(code, params)
      message.success('Stock deleted successfully')
      setState({
        ...state,
        stocks: state.stocks.filter((s) => s.code !== code)
      })
    } catch (error) {
      message.error('Failed to delete stock')
      console.error('Failed to delete stock:', error)
      throw error
    }
  }, [state])

  useEffect(() => {
    fetchData(params)
  }, [])

  return {
    ...state,
    fetchStocks: fetchData,
    addStock: addStockFunc,
    deleteStock: deleteStockFunc,
  }
}
