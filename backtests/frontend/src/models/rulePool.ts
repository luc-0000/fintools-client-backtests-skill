import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { Pool, BaseResponseType } from '@/types'
import { ruleService } from '@/services'

type StateType = {
  rulePools: Pool[]
  loading: boolean
}

export type RulePoolParams = {
  rule_id?: number
}

export const useRulePoolModel = (params: RulePoolParams = {}) => {
  const initState: StateType = { rulePools: [], loading: true }
  const [state, setState] = useState<StateType>(initState)

  const fetchData = useCallback(async (params: RulePoolParams) => {
    if (!params.rule_id) {
      setState({ ...initState, loading: false })
      return
    }

    setState({ ...state, loading: true })
    try {
      const response = await ruleService.getRulePools(params.rule_id, {}) as BaseResponseType<Pool[]>
      if (response.code === 'SUCCESS') {
        setState({
          rulePools: response.data || [],
          loading: false
        })
      } else {
        message.error(response.errMsg || 'Failed to fetch rule pools')
        setState({ ...initState, loading: false })
      }
    } catch (error) {
      message.error('Failed to fetch rule pools')
      console.error('Failed to fetch rule pools:', error)
      setState({ ...initState, loading: false })
    }
  }, [])

  const addPoolToRuleFunc = useCallback(async (ruleId: number, poolIds: number[]) => {
    try {
      await ruleService.addPoolsToRule(ruleId, { pool_ids: poolIds })
      message.success('Pools added to rule successfully')
      await fetchData(params)
    } catch (error) {
      message.error('Failed to add pools to rule')
      console.error('Failed to add pools to rule:', error)
      throw error
    }
  }, [params])

  const deletePoolFromRuleFunc = useCallback(async (ruleId: number, poolId: number) => {
    try {
      await ruleService.deletePoolFromRule(ruleId, { pool_id: poolId })
      message.success('Pool removed from rule successfully')
      await fetchData(params)
    } catch (error) {
      message.error('Failed to remove pool from rule')
      console.error('Failed to remove pool from rule:', error)
      throw error
    }
  }, [params])

  useEffect(() => {
    fetchData(params)
  }, [params.rule_id])

  return {
    ...state,
    fetchRulePools: fetchData,
    addPoolToRuleFunc,
    deletePoolFromRuleFunc,
  }
}
