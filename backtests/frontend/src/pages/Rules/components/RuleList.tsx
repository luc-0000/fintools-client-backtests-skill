import { Link } from 'react-router-dom'
import { ProTable, ProForm, ProFormText } from '@ant-design/pro-components'
import { Button, Divider, Modal, Spin, Tag, Collapse, message } from 'antd'
import { useState, useEffect } from 'react'
import type { Rule } from '@/types'
import { useRuleListModel } from '@/models'
import PopupForm from '@/components/PopupForm'
import { agentService } from '@/services'

type StockIndicating = {
  code: string
  name: string
  indicating: boolean | null
  executed_at: string | null
  last_executed_at: string | null
}

type RuleStocksData = {
  [ruleId: number]: {
    stocks: StockIndicating[]
    lastRunTime: string | null
    loading: boolean
    executedCount: number  // Number of stocks executed today
    totalCount: number  // Total number of stocks
  }
}

type RuleListProps = {
  ruleType: 'remote_agent'
}

const RuleList: React.FC<RuleListProps> = ({ ruleType }) => {
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [deleteModalVisible, setDeleteModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [currentRule, setCurrentRule] = useState<Rule | undefined>()
  const [mainFilePath, setMainFilePath] = useState<string>('')
  const [editMainFilePath, setEditMainFilePath] = useState<string>('')
  const [ruleStocksData, setRuleStocksData] = useState<RuleStocksData>({})

  const { rules, total, loading, addRuleFunc, deleteRuleFunc, editRuleFunc } = useRuleListModel({ rule_type: ruleType })

  // Fetch stocks indicating status for a rule
  const fetchRuleStocksIndicating = async (ruleId: number, forceRefresh = false) => {
    if (!forceRefresh && ruleStocksData[ruleId]?.stocks) {
      // Already loaded, don't fetch again unless forced
      return
    }

    setRuleStocksData(prev => ({
      ...prev,
      [ruleId]: {
        stocks: prev[ruleId]?.stocks || [],
        lastRunTime: prev[ruleId]?.lastRunTime || null,
        loading: true,
        executedCount: prev[ruleId]?.executedCount || 0,
        totalCount: prev[ruleId]?.totalCount || 0
      }
    }))

    try {
      const response = await agentService.getRuleStocksIndicating(ruleId) as any
      if (response?.code === 'SUCCESS') {
        setRuleStocksData(prev => ({
          ...prev,
          [ruleId]: {
            stocks: response.data.items || [],
            lastRunTime: response.data.last_run_time,
            loading: false,
            executedCount: response.data.executed_count || 0,
            totalCount: response.data.total_count || 0
          }
        }))
      }
    } catch (error) {
      console.error('Failed to fetch stocks indicating:', error)
      setRuleStocksData(prev => ({
        ...prev,
        [ruleId]: {
          stocks: prev[ruleId]?.stocks || [],
          lastRunTime: prev[ruleId]?.lastRunTime || null,
          loading: false,
          executedCount: prev[ruleId]?.executedCount || 0,
          totalCount: prev[ruleId]?.totalCount || 0
        }
      }))
    }
  }

  // Auto-load progress for all rules when they are loaded
  useEffect(() => {
    if (rules.length > 0) {
      rules.forEach(rule => {
        if (rule.id && !ruleStocksData[rule.id]?.stocks) {
          fetchRuleStocksIndicating(rule.id)
        }
      })
    }
  }, [rules])

  const columns = [
    {
      dataIndex: 'agent_id',
      width: '8%',
      title: 'Agent ID',
      render: (_: any, record: Rule) => record.agent_id || '-',
    },
    {
      dataIndex: 'name',
      width: '10%',
      title: 'Name',
      render: (_: any, record: Rule) => (
        <Link to={`/rule/${record.id}`} state={{ name: record.name, bindKey: 'cn_stocks', ruleType: 'agent' }}>
          {record.name}
        </Link>
      ),
    },
    { dataIndex: 'pools', width: '10%', title: 'Pools' },
    { dataIndex: 'stocks', width: '5%', title: 'Stocks' },
    {
      dataIndex: 'today_progress',
      width: '10%',
      title: "Today's Progress",
      render: (_: any, record: Rule) => {
        const data = ruleStocksData[record.id || 0]
        if (!data || data.loading) {
          return <span style={{ color: '#999' }}>Loading...</span>
        }
        const { executedCount, totalCount } = data
        const percentage = totalCount > 0 ? Math.round((executedCount / totalCount) * 100) : 0
        return (
          <span>
            {executedCount}/{totalCount} ({percentage}%)
          </span>
        )
      }
    },
    { dataIndex: 'description', width: '15%', title: 'Description' },
    { dataIndex: 'updated_at', width: '15%', title: 'Updated At', valueType: 'dateTime' as const },
    {
      dataIndex: 'operator',
      title: 'Actions',
      render: (_: any, record: Rule) => (
        <>
          <a
            onClick={async () => {
              if (record.id) {
                try {
                  const response = await agentService.startRuleExecution(record.id)
                  if (response && (response.code === 'SUCCESS')) {
                    const executionId = response.execution_id || response.data?.execution_id
                    if (executionId) {
                      const url = `/agent-log/${record.id}?execution_id=${executionId}`
                      window.open(url, '_blank')
                    } else {
                      message.error('No execution_id in response')
                    }
                  } else {
                    message.error(`Failed to start execution: ${response?.message || 'Unknown error'}`)
                  }
                } catch (error) {
                  message.error('Failed to start execution')
                }
              }
            }}
          >
            Run Today
          </a>
          <Divider type="vertical" />
          <a onClick={() => {
            setCurrentRule(record)
            setEditMainFilePath(record.info || '')
            setEditModalVisible(true)
          }}>Edit</a>
          <Divider type="vertical" />
          <a onClick={() => { setCurrentRule(record); setDeleteModalVisible(true) }}>Delete</a>
        </>
      ),
    },
  ]

  // Expandable row config
  const expandable = {
    expandedRowRender: (record: Rule) => {
      const ruleId = record.id
      const data = ruleStocksData[ruleId || 0]

      if (!data) {
        return <div style={{ padding: '16px' }}>Click to load stocks</div>
      }

      if (data.loading) {
        return <div style={{ padding: '16px' }}><Spin size="small" /> Loading...</div>
      }

      const { stocks, executedCount, totalCount } = data

      return (
        <div style={{ padding: '16px' }}>
          <div style={{ marginBottom: '12px', display: 'flex', gap: '20px' }}>
            <span><strong>Today's Progress:</strong> {executedCount}/{totalCount}</span>
            <span><strong>Last Run Time:</strong> {data.lastRunTime ? new Date(data.lastRunTime).toLocaleString() : 'Never run'}</span>
          </div>
          <Collapse
            items={[
              {
                key: '1',
                label: `Stocks Indicating Status (${stocks.length} stocks)`,
                children: (
                  <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                    {stocks.length === 0 ? (
                      <div>No stocks found</div>
                    ) : (
                      stocks.map((stock) => {
                        return (
                          <div
                            key={stock.code}
                            style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              padding: '8px 12px',
                              borderBottom: '1px solid #f0f0f0'
                            }}
                          >
                            <div style={{ flex: 1 }}>
                              <strong>{stock.code}</strong> - {stock.name}
                              {stock.last_executed_at ? (
                                <span style={{ marginLeft: '12px', fontSize: '12px', color: '#999' }}>
                                  Last Run: {new Date(stock.last_executed_at).toLocaleString()}
                                </span>
                              ) : (
                                <span style={{ marginLeft: '12px', fontSize: '12px', color: '#999' }}>
                                  Last Run: Never
                                </span>
                              )}
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                              {!stock.last_executed_at ? (
                                <Tag color="default">Never Run</Tag>
                              ) : stock.indicating === null ? (
                                <Tag color="default">Not Run Today</Tag>
                              ) : stock.indicating ? (
                                <Tag color="green">Indicating</Tag>
                              ) : (
                                <Tag color="red">Not Indicating</Tag>
                              )}
                              <Button
                                size="small"
                                type="primary"
                                onClick={async () => {
                                  try {
                                    const response = await agentService.startStockExecution(ruleId!, stock.code) as any
                                    if (response?.code === 'SUCCESS') {
                                      const executionId = response.execution_id || response.data?.execution_id
                                      if (executionId) {
                                        const url = `/agent-log/${ruleId}/${stock.code}?execution_id=${executionId}`
                                        window.open(url, '_blank')
                                      } else {
                                        message.error('No execution_id in response')
                                      }
                                    } else {
                                      message.error(`Failed to start execution: ${response?.message || 'Unknown error'}`)
                                    }
                                  } catch (error) {
                                    message.error('Failed to start execution')
                                  }
                                }}
                              >
                                Run
                              </Button>
                            </div>
                          </div>
                        )
                      })
                    )}
                  </div>
                ),
              },
            ]}
            defaultActiveKey={[]}
          />
        </div>
      )
    },
    onExpand: (expanded: boolean, record: Rule) => {
      if (expanded && record.id) {
        fetchRuleStocksIndicating(record.id)
      }
    },
  }

  const handleCreateSubmit = async (values: any) => {
    await addRuleFunc({
      name: values.name,
      agent_id: values.agent_id,
      description: values.description?.trim() || undefined,
      info: mainFilePath,
      type: ruleType,
    })
    setCreateModalVisible(false)
    setMainFilePath('')
  }

  return (
    <Spin spinning={loading}>
      <ProTable<Rule>
        dataSource={rules}
        rowKey="id"
        pagination={{ pageSize: 50, total }}
        columns={columns}
        search={false}
        scroll={{ x: 1200, y: 600 }}
        expandable={expandable}
        toolBarRender={() => [
          <Button key="1" type="primary" onClick={() => setCreateModalVisible(true)}>
            Create
          </Button>
        ]}
      />
      <Modal title="Create Remote Agent" open={createModalVisible} onCancel={() => { setCreateModalVisible(false); setMainFilePath('') }} footer={null}>
        <ProForm onFinish={handleCreateSubmit}>
          <ProFormText name="name" label="Name" required />
          <ProFormText
            name="agent_id"
            label="Agent ID"
            placeholder="105"
            required
          />
          <ProFormText
            name="main_file"
            label="A2A URL"
            placeholder="http://localhost:8000/v1/a2a/agent"
            required
            fieldProps={{
              value: mainFilePath,
              onChange: (e: React.ChangeEvent<HTMLInputElement>) => setMainFilePath(e.target.value),
            }}
          />
          <ProFormText name="description" label="Description" />
          <ProFormText
            name="type"
            label="Type"
            initialValue={ruleType}
            disabled
            fieldProps={{
              value: ruleType
            }}
          />
        </ProForm>
      </Modal>
      <Modal
        title="Delete"
        open={deleteModalVisible}
        onOk={() => { if (currentRule?.id) { deleteRuleFunc(currentRule.id) } setDeleteModalVisible(false) }}
        onCancel={() => setDeleteModalVisible(false)}
      >
        Are you sure you want to delete rule {currentRule?.name}?
      </Modal>
      <PopupForm
        onCancel={() => setEditModalVisible(false)}
        modalVisible={editModalVisible}
        formTitle="Edit"
      >
        <ProForm
          onFinish={(values) => {
            if (currentRule?.id) {
              editRuleFunc(currentRule.id, {
                name: values.name,
                description: values.description?.trim() || undefined,
                info: editMainFilePath,
              })
            }
            setEditModalVisible(false)
          }}
        >
          <ProFormText width="md" name="name" label="Name" initialValue={currentRule?.name} required />
          <ProFormText
            width="md"
            name="main_file"
            label="A2A URL"
            placeholder="http://localhost:8000/v1/a2a/agent"
            required
            fieldProps={{
              value: editMainFilePath,
              onChange: (e: React.ChangeEvent<HTMLInputElement>) => setEditMainFilePath(e.target.value),
            }}
          />
          <ProFormText width="md" name="description" label="Description" initialValue={currentRule?.description} />
        </ProForm>
      </PopupForm>
    </Spin>
  )
}

export default RuleList
