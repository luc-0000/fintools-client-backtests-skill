import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { StockRuleEarn, BaseResponseType } from '@/types'
import { ruleService } from '@/services'

type StateType = {
  ruleStocks: StockRuleEarn[]
  loading: boolean
}

export type RuleStockParams = {
  rule_id?: number
}

export const useRuleStockModel = (params: RuleStockParams = {}) => {
  const initState: StateType = { ruleStocks: [], loading: true }
  const [state, setState] = useState<StateType>(initState)

  const fetchData = useCallback(async (params: RuleStockParams) => {
    if (!params.rule_id) {
      setState({ ...initState, loading: false })
      return
    }

    setState({ ...state, loading: true })
    try {
      const response = await ruleService.getRuleStocks(params.rule_id, {}) as BaseResponseType<{ items: StockRuleEarn[] }>
      if (response.code === 'SUCCESS') {
        setState({
          ruleStocks: response.data.items || [],
          loading: false
        })
      } else {
        message.error(response.errMsg || 'Failed to fetch rule stocks')
        setState({ ...initState, loading: false })
      }
    } catch (error) {
      message.error('Failed to fetch rule stocks')
      console.error('Failed to fetch rule stocks:', error)
      setState({ ...initState, loading: false })
    }
  }, [])

  useEffect(() => {
    fetchData(params)
  }, [params.rule_id])

  return {
    ...state,
    fetchRuleStocks: fetchData,
  }
}
