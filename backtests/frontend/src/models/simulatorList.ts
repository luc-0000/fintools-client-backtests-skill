import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { Simulator, BaseResponseType } from '@/types'
import { simulatorService } from '@/services'

type StateType = {
  simulators: Simulator[]
  total: number
  loading: boolean
  updating: boolean
  running: number | null  // Track which simulator is currently running
}

export type SimulatorListParams = {
  current?: number
  pageSize?: number
  rule_type?: string
  [key: string]: any  // Allow additional properties
}

export const useSimulatorListModel = (params: SimulatorListParams = {}) => {
  const initState: StateType = { simulators: [], total: 0, loading: true, updating: false, running: null }
  const [state, setState] = useState<StateType>(initState)

  const fetchData = useCallback(async (params: SimulatorListParams) => {
    setState({ ...state, loading: true, updating: false, running: state.running })
    try {
      const response = await simulatorService.getSimulatorList(params) as BaseResponseType<{ items: Simulator[], total: number }>
      if (response.code === 'SUCCESS') {
        setState({
          simulators: response.data.items || [],
          total: response.data.total || 0,
          loading: false,
          updating: false,
          running: null
        })
      } else if (Array.isArray(response)) {
        setState({ simulators: response, total: response.length, loading: false, updating: false, running: null })
      } else {
        setState({ simulators: [], total: 0, loading: false, updating: false, running: null })
      }
    } catch (error) {
      message.error('Failed to fetch simulators')
      console.error('Failed to fetch simulators:', error)
      setState({ ...initState, loading: false })
    }
  }, [])

  const addSimulatorFunc = useCallback(async (simulator: Partial<Simulator>) => {
    try {
      await simulatorService.addSimulator(simulator)
      message.success('Simulator added successfully')
      await fetchData(params)
    } catch (error) {
      message.error('Failed to add simulator')
      console.error('Failed to add simulator:', error)
      throw error
    }
  }, [params])

  const deleteSimulatorFunc = useCallback(async (id: number) => {
    try {
      await simulatorService.deleteSimulator(id)
      message.success('Simulator deleted successfully')
      setState({
        ...state,
        simulators: state.simulators.filter((s) => s.id !== id)
      })
    } catch (error) {
      message.error('Failed to delete simulator')
      console.error('Failed to delete simulator:', error)
      throw error
    }
  }, [state])

  const runSimulator = useCallback(async (id: number) => {
    try {
      setState(prev => ({ ...prev, running: id }))
      await simulatorService.runSimulator(id)
      message.success('Simulator run started successfully')
      setState(prev => ({ ...prev, running: null }))
      await fetchData(params)
    } catch (error) {
      message.error('Failed to run simulator')
      console.error('Failed to run simulator:', error)
      setState(prev => ({ ...prev, running: null }))
      throw error
    }
  }, [params])

  useEffect(() => {
    fetchData(params)
  }, [params.rule_type])  // Refetch when rule_type changes

  return {
    ...state,
    fetchSimulatorlist: fetchData,
    addSimulatorFunc,
    deleteSimulatorFunc,
    runSimulator,
  }
}
