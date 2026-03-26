import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import type { SimTrading } from '@/types'
import { simulatorService } from '@/services'

export const useSimulatorLogModel = (simId: number) => {
  const [log, setLog] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const fetchLog = useCallback(async () => {
    setLoading(true)
    try {
      const response = await simulatorService.getSimulator(simId) as any
      if (response && response.log_data) {
        setLog(response.log_data)
      }
    } catch (error) {
      message.error('Failed to fetch simulator log')
      console.error('Failed to fetch simulator log:', error)
    } finally {
      setLoading(false)
    }
  }, [simId])

  useEffect(() => {
    if (simId) {
      fetchLog()
    }
  }, [simId])

  return { log, loading, fetchLog }
}

export const useSimulatorParamsModel = (simId: number) => {
  const [params, setParams] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const fetchParams = useCallback(async () => {
    setLoading(true)
    try {
      const response = await simulatorService.getSimulatorParams(simId, {}) as any
      if (response && response.data && response.data.items) {
        setParams(response.data.items)
      }
    } catch (error) {
      message.error('Failed to fetch simulator params')
      console.error('Failed to fetch simulator params:', error)
    } finally {
      setLoading(false)
    }
  }, [simId])

  useEffect(() => {
    if (simId) {
      fetchParams()
    }
  }, [simId])

  return { params, loading, fetchParams }
}

export const useSimulatorTradingModel = (simId: number, pageSize: number = 100) => {
  const [trading, setTrading] = useState<SimTrading[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [stocks, setStocks] = useState<string[]>([])

  const fetchTrading = useCallback(async (page: number = 1, extraParams: any = {}) => {
    setLoading(true)
    try {
      const response = await simulatorService.getSimulatorTrading(simId, {
        page,
        page_size: pageSize,
        ...extraParams,
      }) as any
      if (response && response.data) {
        setTrading(response.data.items || [])
        setTotal(response.data.total || 0)
        if (response.data.stocks) {
          setStocks(response.data.stocks)
        }
      } else {
        setTrading([])
        setTotal(0)
      }
    } catch (error) {
      message.error('Failed to fetch simulator trading')
      console.error('Failed to fetch simulator trading:', error)
    } finally {
      setLoading(false)
    }
  }, [simId, pageSize])

  useEffect(() => {
    if (simId) {
      fetchTrading()
    }
  }, [simId])

  return { trading, total, loading, stocks, fetchTrading }
}
