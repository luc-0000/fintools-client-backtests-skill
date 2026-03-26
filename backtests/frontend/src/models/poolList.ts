import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { Pool, BaseResponseType } from '@/types'
import { poolService } from '@/services'

type StateType = {
  pools: Pool[]
  total: number
  loading: boolean
}

export type PoolListParams = {
  current?: number
  pageSize?: number
}

export const usePoolListModel = (params: PoolListParams = {}) => {
  const initState: StateType = { pools: [], total: 0, loading: true }
  const [state, setState] = useState<StateType>(initState)

  const fetchData = useCallback(async (params: PoolListParams) => {
    setState({ ...state, loading: true })
    try {
      const response = await poolService.getPoolList(params) as BaseResponseType<{ items: Pool[], total: number }>
      if (response.code === 'SUCCESS') {
        setState({
          pools: response.data.items || [],
          total: response.data.total || 0,
          loading: false
        })
      } else if (Array.isArray(response)) {
        setState({ pools: response, total: response.length, loading: false })
      } else {
        setState({ pools: [], total: 0, loading: false })
      }
    } catch (error) {
      message.error('Failed to fetch pools')
      console.error('Failed to fetch pools:', error)
      setState({ ...initState, loading: false })
    }
  }, [])

  const addPoolFunc = useCallback(async (pool: Partial<Pool>) => {
    try {
      await poolService.addPool(pool)
      message.success('Pool added successfully')
      await fetchData(params)
    } catch (error) {
      message.error('Failed to add pool')
      console.error('Failed to add pool:', error)
      throw error
    }
  }, [params])

  const updatePoolFunc = useCallback(async (id: number, data: Partial<Pool>) => {
    try {
      await poolService.updatePool(id, data)
      message.success('Pool updated successfully')
      setState({
        ...state,
        pools: state.pools.map((p) => (p.id === id ? { ...p, ...data } : p))
      })
    } catch (error) {
      message.error('Failed to update pool')
      console.error('Failed to update pool:', error)
      throw error
    }
  }, [state])

  const deletePoolFunc = useCallback(async (id: number) => {
    try {
      await poolService.deletePool(id)
      message.success('Pool deleted successfully')
      setState({
        ...state,
        pools: state.pools.filter((p) => p.id !== id)
      })
    } catch (error) {
      message.error('Failed to delete pool')
      console.error('Failed to delete pool:', error)
      throw error
    }
  }, [state])

  useEffect(() => {
    fetchData(params)
  }, [])

  return {
    ...state,
    fetchPools: fetchData,
    addPool: addPoolFunc,
    updatePool: updatePoolFunc,
    deletePool: deletePoolFunc,
  }
}
