import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { BaseResponseType } from '@/types'
import { ruleService } from '@/services'

type StateType = {
  ruleParams: any[]
  loading: boolean
}

export type RuleParamsParams = {
  rule_id?: number
}

export const useRuleParamsModel = (params: RuleParamsParams = {}) => {
  const initState: StateType = { ruleParams: [], loading: true }
  const [state, setState] = useState<StateType>(initState)

  const fetchData = useCallback(async (params: RuleParamsParams) => {
    if (!params.rule_id) {
      setState({ ...initState, loading: false })
      return
    }

    setState({ ...state, loading: true })
    try {
      const response = await ruleService.getRuleParams(params.rule_id, {}) as BaseResponseType<{ items: any[] }>
      if (response.code === 'SUCCESS') {
        setState({
          ruleParams: response.data.items || [],
          loading: false
        })
      } else {
        message.error(response.errMsg || 'Failed to fetch rule params')
        setState({ ...initState, loading: false })
      }
    } catch (error) {
      message.error('Failed to fetch rule params')
      console.error('Failed to fetch rule params:', error)
      setState({ ...initState, loading: false })
    }
  }, [])

  useEffect(() => {
    fetchData(params)
  }, [params.rule_id])

  return {
    ...state,
    fetchRuleParams: fetchData,
  }
}
