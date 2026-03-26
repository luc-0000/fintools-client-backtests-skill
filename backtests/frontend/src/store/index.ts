import { create } from 'zustand'

// 全局状态
interface GlobalState {
  collapsed: boolean
  setCollapsed: (collapsed: boolean) => void
}

export const useGlobalStore = create<GlobalState>((set) => ({
  collapsed: false,
  setCollapsed: (collapsed) => set({ collapsed }),
}))

// 统一导出所有 store
export { usePoolStore } from './pool'
export { useStockStore } from './stock'
export { useSimulatorStore } from './simulator'
export { useRuleStore } from './rule'
