import { create } from 'zustand'
import type { Rule, StockRuleEarn, PageParams } from '@/types'
import { ruleService } from '@/services'

interface RuleState {
  rules: Rule[]
  ruleStocks: StockRuleEarn[]
  ruleParams: any[]
  total: number
  loading: boolean
  fetchRules: (params?: PageParams) => Promise<void>
  fetchRuleStocks: (params?: any) => Promise<void>
  fetchRuleParams: (params?: any) => Promise<void>
  addRule: (rule: Partial<Rule>) => Promise<void>
  updateRule: (id: number, data: Partial<Rule>) => Promise<void>
  deleteRule: (id: number) => Promise<void>
}

export const useRuleStore = create<RuleState>((set, get) => ({
  rules: [],
  ruleStocks: [],
  ruleParams: [],
  total: 0,
  loading: false,

  fetchRules: async (params = {}) => {
    set({ loading: true })
    try {
      const response = await ruleService.getRuleList(params)
      if (response && response.data && response.data.items) {
        set({
          rules: response.data.items,
          total: response.data.total,
          loading: false
        })
      } else if (Array.isArray(response)) {
        set({ rules: response, total: response.length, loading: false })
      } else {
        set({ rules: [], total: 0, loading: false })
      }
    } catch (error) {
      console.error('Failed to fetch rules:', error)
      set({ loading: false })
    }
  },

  fetchRuleStocks: async (params = {}) => {
    set({ loading: true })
    try {
      const response = await ruleService.getRuleStocks(1, params)
      if (response && response.data && response.data.items) {
        set({ ruleStocks: response.data.items, loading: false })
      } else {
        set({ ruleStocks: [], loading: false })
      }
    } catch (error) {
      console.error('Failed to fetch rule stocks:', error)
      set({ loading: false })
    }
  },

  fetchRuleParams: async (params = {}) => {
    set({ loading: true })
    try {
      const response = await ruleService.getRuleParams(1, params)
      if (response && response.data && response.data.items) {
        set({ ruleParams: response.data.items, loading: false })
      } else {
        set({ ruleParams: [], loading: false })
      }
    } catch (error) {
      console.error('Failed to fetch rule params:', error)
      set({ loading: false })
    }
  },

  addRule: async (rule) => {
    try {
      await ruleService.addRule(rule)
      get().fetchRules()
    } catch (error) {
      console.error('Failed to add rule:', error)
      throw error
    }
  },

  updateRule: async (id, data) => {
    try {
      await ruleService.updateRule(id, data)
      const { rules } = get()
      set({ rules: rules.map((r) => (r.id === id ? { ...r, ...data } : r)) })
    } catch (error) {
      console.error('Failed to update rule:', error)
      throw error
    }
  },

  deleteRule: async (id) => {
    try {
      await ruleService.deleteRule(id)
      const { rules } = get()
      set({ rules: rules.filter((r) => r.id !== id) })
    } catch (error) {
      console.error('Failed to delete rule:', error)
      throw error
    }
  },
}))
