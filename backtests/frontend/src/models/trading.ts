import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { Tradings, TradeEarn, BaseResponseType, PageParams } from '@/types'
import { simulatorService } from '@/services'

type TradingStateType = {
  tradings: Tradings[]
  loading: boolean
}

export const useTradingListModel = (params: PageParams = {}) => {
  const initState: TradingStateType = { tradings: [], loading: true }
  const [state, setState] = useState<TradingStateType>(initState)

  const fetchData = useCallback(async (params: PageParams) => {
    setState({ ...state, loading: true })
    try {
      const response = await simulatorService.getTradings(params) as BaseResponseType<{ items: Tradings[] }>
      if (response.code === 'SUCCESS') {
        setState({
          tradings: response.data.items || [],
          loading: false
        })
      } else {
        setState({ ...initState, loading: false })
      }
    } catch (error) {
      message.error('Failed to fetch tradings')
      console.error('Failed to fetch tradings:', error)
      setState({ ...initState, loading: false })
    }
  }, [])

  useEffect(() => {
    fetchData(params)
  }, [])

  return {
    ...state,
    fetchTradings: fetchData,
  }
}

type TradeEarnStateType = {
  tradeEarns: TradeEarn[]
  loading: boolean
}

export const useTradeEarnListModel = (params: PageParams = {}) => {
  const initState: TradeEarnStateType = { tradeEarns: [], loading: true }
  const [state, setState] = useState<TradeEarnStateType>(initState)

  const fetchData = useCallback(async (params: PageParams) => {
    setState({ ...state, loading: true })
    try {
      const response = await simulatorService.getTradeEarns(params) as BaseResponseType<{ items: TradeEarn[] }>
      if (response.code === 'SUCCESS') {
        setState({
          tradeEarns: response.data.items || [],
          loading: false
        })
      } else {
        setState({ ...initState, loading: false })
      }
    } catch (error) {
      message.error('Failed to fetch trade earns')
      console.error('Failed to fetch trade earns:', error)
      setState({ ...initState, loading: false })
    }
  }, [])

  useEffect(() => {
    fetchData(params)
  }, [])

  return {
    ...state,
    fetchTradeEarns: fetchData,
  }
}
