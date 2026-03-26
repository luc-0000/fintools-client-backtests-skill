import { create } from 'zustand'
import type { Simulator, PageParams } from '@/types'
import { simulatorService } from '@/services'

interface SimulatorState {
  simulators: Simulator[]
  tradings: any[]
  tradeEarns: any[]
  total: number
  loading: boolean
  updating: boolean
  fetchSimulators: (params?: PageParams) => Promise<void>
  addSimulator: (simulator: Partial<Simulator>) => Promise<void>
  deleteSimulator: (id: number) => Promise<void>
  updateSimulator: (id: number, data?: any) => Promise<void>
  runSimulator: (id: number, data?: any) => Promise<void>
  fetchTradings: (params?: PageParams) => Promise<void>
  fetchTradeEarns: (params?: PageParams) => Promise<void>
}

export const useSimulatorStore = create<SimulatorState>((set, get) => ({
  simulators: [],
  tradings: [],
  tradeEarns: [],
  total: 0,
  loading: false,
  updating: false,

  fetchSimulators: async (params = {}) => {
    set({ loading: true })
    try {
      const response = await simulatorService.getSimulatorList(params)
      if (response && response.data && response.data.items) {
        set({
          simulators: response.data.items,
          total: response.data.total,
          loading: false
        })
      } else if (Array.isArray(response)) {
        set({ simulators: response, total: response.length, loading: false })
      } else {
        set({ simulators: [], total: 0, loading: false })
      }
    } catch (error) {
      console.error('Failed to fetch simulators:', error)
      set({ loading: false })
    }
  },

  addSimulator: async (simulator) => {
    try {
      await simulatorService.addSimulator(simulator)
      get().fetchSimulators()
    } catch (error) {
      console.error('Failed to add simulator:', error)
      throw error
    }
  },

  deleteSimulator: async (id) => {
    try {
      await simulatorService.deleteSimulator(id)
      const { simulators } = get()
      set({ simulators: simulators.filter((s) => s.id !== id) })
    } catch (error) {
      console.error('Failed to delete simulator:', error)
      throw error
    }
  },

  updateSimulator: async (id, data) => {
    try {
      set({ updating: true })
      await simulatorService.updateSimulator(id, data)
      get().fetchSimulators()
    } catch (error) {
      console.error('Failed to update simulator:', error)
      set({ updating: false })
      throw error
    }
  },

  runSimulator: async (id, _data?) => {
    try {
      await simulatorService.runSimulator(id)
      get().fetchSimulators()
    } catch (error) {
      console.error('Failed to run simulator:', error)
      throw error
    }
  },

  fetchTradings: async (params = {}) => {
    set({ loading: true })
    try {
      const response = await simulatorService.getTradings(params)
      if (response && response.data && response.data.items) {
        set({ tradings: response.data.items, loading: false })
      } else {
        set({ tradings: [], loading: false })
      }
    } catch (error) {
      console.error('Failed to fetch tradings:', error)
      set({ loading: false })
    }
  },

  fetchTradeEarns: async (params = {}) => {
    set({ loading: true })
    try {
      const response = await simulatorService.getTradeEarns(params)
      if (response && response.data && response.data.items) {
        set({ tradeEarns: response.data.items, loading: false })
      } else {
        set({ tradeEarns: [], loading: false })
      }
    } catch (error) {
      console.error('Failed to fetch trade earns:', error)
      set({ loading: false })
    }
  },
}))
