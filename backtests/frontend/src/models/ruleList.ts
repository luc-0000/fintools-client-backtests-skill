import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { Rule, BaseResponseType } from '@/types'
import { ruleService, agentService } from '@/services'

type StateType = {
  rules: Rule[]
  total: number
  loading: boolean
  running: number | null  // Track which rule is currently running
}

export type RuleListParams = {
  rule_type?: string
}

export const useRuleListModel = (params: RuleListParams = {}) => {
  const initState: StateType = { rules: [], total: 0, loading: true, running: null }
  const [state, setState] = useState<StateType>(initState)

  const fetchData = useCallback(async (params: RuleListParams) => {
    setState(prev => ({ ...prev, loading: true }))
    try {
      const response = await ruleService.getRuleList(params) as BaseResponseType<{ items: Rule[], total: number }>
      if (response.code === 'SUCCESS') {
        setState({
          rules: response.data.items || [],
          total: response.data.total || 0,
          loading: false,
          running: null
        })
      } else {
        message.error(response.errMsg || 'Failed to fetch rules')
        setState({ ...initState, loading: false })
      }
    } catch (error) {
      message.error('Failed to fetch rules')
      console.error('Failed to fetch rules:', error)
      setState({ ...initState, loading: false })
    }
  }, [])

  const addRuleFunc = useCallback(async (rule: Partial<Rule>) => {
    try {
      await ruleService.addRule(rule)
      message.success('Rule added successfully')
      await fetchData(params)
    } catch (error) {
      message.error('Failed to add rule')
      console.error('Failed to add rule:', error)
      throw error
    }
  }, [params])

  const editRuleFunc = useCallback(async (id: number, data: Partial<Rule>) => {
    try {
      await ruleService.updateRule(id, data)
      message.success('Rule updated successfully')
      setState({
        ...state,
        rules: state.rules.map((r) => (r.id === id ? { ...r, ...data } : r))
      })
    } catch (error) {
      message.error('Failed to update rule')
      console.error('Failed to update rule:', error)
      throw error
    }
  }, [state])

  const deleteRuleFunc = useCallback(async (id: number) => {
    try {
      await ruleService.deleteRule(id)
      message.success('Rule deleted successfully')
      setState({
        ...state,
        rules: state.rules.filter((r) => r.id !== id)
      })
    } catch (error) {
      message.error('Failed to delete rule')
      console.error('Failed to delete rule:', error)
      throw error
    }
  }, [state])

  const runRuleFunc = useCallback(async (id: number) => {
    try {
      setState(prev => ({ ...prev, running: id }))
      await agentService.runAgent(id)
      message.success('Agent running started successfully')
      setState(prev => ({ ...prev, running: null }))
    } catch (error) {
      message.error('Failed to run agent')
      console.error('Failed to run agent:', error)
      setState(prev => ({ ...prev, running: null }))
      throw error
    }
  }, [])

  useEffect(() => {
    fetchData(params)
  }, [params.rule_type])

  return {
    ...state,
    fetchRules: fetchData,
    addRuleFunc,
    editRuleFunc,
    deleteRuleFunc,
    runRuleFunc,
  }
}
