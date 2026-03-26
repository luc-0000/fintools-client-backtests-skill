import { create } from 'zustand'
import type { Stock, PageParams } from '@/types'
import { stockService } from '@/services'

interface StockState {
  stocks: Stock[]
  total: number
  loading: boolean
  fetchStocks: (params?: PageParams) => Promise<void>
  addStock: (stock: Partial<Stock>) => Promise<void>
  deleteStock: (code: string, params?: PageParams) => Promise<void>
}

export const useStockStore = create<StockState>((set, get) => ({
  stocks: [],
  total: 0,
  loading: false,

  fetchStocks: async (params = {}) => {
    set({ loading: true })
    try {
      const response = await stockService.getStockList(params)
      if (response && response.data && response.data.items) {
        set({
          stocks: response.data.items,
          total: response.data.total,
          loading: false
        })
      } else if (Array.isArray(response)) {
        set({ stocks: response, total: response.length, loading: false })
      } else {
        set({ stocks: [], total: 0, loading: false })
      }
    } catch (error) {
      console.error('Failed to fetch stocks:', error)
      set({ loading: false })
    }
  },

  addStock: async (stock) => {
    try {
      await stockService.addStock(stock)
      get().fetchStocks()
    } catch (error) {
      console.error('Failed to add stock:', error)
      throw error
    }
  },

  deleteStock: async (code, params) => {
    try {
      await stockService.deleteStock(code, params)
      const { stocks } = get()
      set({ stocks: stocks.filter((s) => s.code !== code) })
    } catch (error) {
      console.error('Failed to delete stock:', error)
      throw error
    }
  },
}))
