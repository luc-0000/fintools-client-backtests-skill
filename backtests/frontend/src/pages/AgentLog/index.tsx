import { useEffect, useState, useRef } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Typography, Spin, Button, Space, Tag, message } from 'antd'

const { Title } = Typography

type LogEntry = {
  type: string
  message: string
  stock_code?: string
  timestamp?: string
  result?: any
  error?: string
  stocks?: string[]
}

const AgentLog = () => {
  const { ruleId, stockCode } = useParams<{ ruleId: string; stockCode?: string }>()
  const [searchParams] = useSearchParams()
  const [logs, setLogs] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [currentStock, setCurrentStock] = useState<string>('')
  const [completedStocks, setCompletedStocks] = useState<string[]>([])
  const [totalStocks, setTotalStocks] = useState<number>(0)
  const eventSourceRef = useRef<EventSource | null>(null)
  const logContainerRef = useRef<HTMLDivElement>(null)

  // Determine if we're running a single stock or all stocks
  const isSingleStockMode = !!stockCode
  const executionId = searchParams.get('execution_id')

  useEffect(() => {
    if (!ruleId || !executionId) {
      message.error('Missing execution_id')
      setLoading(false)
      return
    }

    // Build SSE endpoint URL with execution_id
    const streamUrl = isSingleStockMode
      ? `/api/v1/get_rule/rule/${ruleId}/stock/${stockCode}/stream?execution_id=${executionId}`
      : `/api/v1/get_rule/rule/${ruleId}/stream?execution_id=${executionId}`

    console.log(`Connecting to SSE: ${streamUrl}`)

    const eventSource = new EventSource(streamUrl)
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      console.log('SSE connection opened')
    }

    eventSource.onmessage = (event) => {
      try {
        const data: LogEntry = JSON.parse(event.data)
        handleLogEntry(data)
      } catch (error) {
        console.error('Failed to parse SSE data:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      setLoading(false)
      message.error('Connection to server lost')
      eventSource.close()
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [ruleId, executionId, stockCode, isSingleStockMode])

  const handleLogEntry = (data: LogEntry) => {
    const timestamp = data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()
    const logMessage = `[${timestamp}] ${data.message}`

    setLogs((prev) => [...prev, logMessage])

    // Auto-scroll to bottom
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }

    // Update state based on event type
    switch (data.type) {
      case 'stock_start':
        setCurrentStock(data.stock_code || '')
        break
      case 'stock_complete':
        setCompletedStocks((prev) => [...new Set([...prev, data.stock_code!])])
        setCurrentStock('')
        setLoading(false)
        break
      case 'stock_error':
        setCompletedStocks((prev) => [...new Set([...prev, data.stock_code!])])
        setCurrentStock('')
        setLoading(false)
        break
      case 'info':
        if (data.stocks) {
          setTotalStocks(data.stocks.length)
        }
        break
      case 'complete':
        setLoading(false)
        message.success('All stocks processed!')
        break
      case 'error':
        setLoading(false)
        message.error(data.message)
        break
    }
  }

  return (
    <div style={{ padding: '24px 48px', backgroundColor: '#141414', minHeight: '100vh', color: '#fff' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <Title level={3} style={{ margin: 0, color: '#fff' }}>
            {isSingleStockMode
              ? `${stockCode} - Execution Log`
              : `Rule ${ruleId} - Execution Log`
            }
          </Title>
          <Space>
            {!isSingleStockMode && (
              <>
                <Tag color="blue">Total: {totalStocks || 0}</Tag>
                <Tag color="green">Completed: {completedStocks.length}</Tag>
                {currentStock && <Tag color="processing">Processing: {currentStock}</Tag>}
              </>
            )}
            <Button danger onClick={() => window.close()}>
              Close
            </Button>
          </Space>
        </div>

        {/* Log Display */}
        <div style={{
          backgroundColor: '#1e1e1e',
          color: '#d4d4d4',
          fontFamily: 'monospace',
          fontSize: '13px',
          padding: '16px',
          borderRadius: '6px',
          overflowY: 'auto',
          maxHeight: '600px'
        }}>
          <div ref={logContainerRef} style={{ minHeight: '200px' }}>
            {logs.length === 0 && loading && (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Spin size="large" />
                <div style={{ marginTop: '16px', color: '#999' }}>Waiting for logs...</div>
              </div>
            )}
            {logs.map((log, index) => (
              <div key={index} style={{ marginBottom: '4px', whiteSpace: 'pre-wrap' }}>
                {log}
              </div>
            ))}
          </div>
        </div>
      </Space>
    </div>
  )
}

export default AgentLog
