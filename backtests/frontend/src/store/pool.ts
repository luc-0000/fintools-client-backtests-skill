import { create } from 'zustand'
import type { Pool, PageParams } from '@/types'
import { poolService } from '@/services'

interface PoolState {
  pools: Pool[]
  total: number
  loading: boolean
  fetchPools: (params?: PageParams) => Promise<void>
  addPool: (pool: Partial<Pool>) => Promise<void>
  updatePool: (id: number, data: Partial<Pool>) => Promise<void>
  deletePool: (id: number) => Promise<void>
}

export const usePoolStore = create<PoolState>((set, get) => ({
  pools: [],
  total: 0,
  loading: false,

  fetchPools: async (params = {}) => {
    set({ loading: true })
    try {
      const response = await poolService.getPoolList(params)
      if (response && response.data && response.data.items) {
        set({
          pools: response.data.items,
          total: response.data.total,
          loading: false
        })
      } else if (Array.isArray(response)) {
        set({ pools: response, total: response.length, loading: false })
      } else {
        set({ pools: [], total: 0, loading: false })
      }
    } catch (error) {
      console.error('Failed to fetch pools:', error)
      set({ loading: false })
    }
  },

  addPool: async (pool) => {
    try {
      await poolService.addPool(pool)
      get().fetchPools()
    } catch (error) {
      console.error('Failed to add pool:', error)
      throw error
    }
  },

  updatePool: async (id, data) => {
    try {
      await poolService.updatePool(id, data)
      const { pools } = get()
      set({ pools: pools.map((p) => (p.id === id ? { ...p, ...data } : p)) })
    } catch (error) {
      console.error('Failed to update pool:', error)
      throw error
    }
  },

  deletePool: async (id) => {
    try {
      await poolService.deletePool(id)
      const { pools } = get()
      set({ pools: pools.filter((p) => p.id !== id) })
    } catch (error) {
      console.error('Failed to delete pool:', error)
      throw error
    }
  },
}))
