import { useParams, useLocation } from 'react-router-dom'
import { Tabs, Spin, Button, Modal, Select } from 'antd'
import { useState, useEffect } from 'react'
import { ProTable } from '@ant-design/pro-components'
import { useRulePoolListModel, useRuleStockListModel, useAllPoolsListModel, useRuleTradingListModel } from '@/models'
import type { Pool, StockRuleEarn, RuleTrading } from '@/types'
import type { CompareFn } from 'antd/es/table/interface'
import { MinRate } from '@/pages/Shared/const'

const PageSize = 50

const RuleDetail = () => {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const state = location.state as { name?: string; bindKey?: string; ruleType?: string } | undefined
  const ruleName = state?.name?.toUpperCase() || `Rule ${id}`
  const ruleId = parseInt(id || '0')
  const initBindKey = state?.bindKey || 'cn_stocks'

  const [bindKey] = useState<string>(initBindKey)
  const [currentTab, setCurrentTab] = useState<string>('1')

  // Pools related state
  const [addPoolModalVisible, setAddPoolModalVisible] = useState(false)
  const [selectedPoolIds, setSelectedPoolIds] = useState<number[]>([])

  // Stocks related state
  const [selectedPoolId, setSelectedPoolId] = useState<number | undefined>()

  // Agent Trading related state
  const [tradingCurrentPage, setTradingCurrentPage] = useState(1)

  // Use models
  const { pools: rulePools, total: poolsTotal, loading: poolsLoading, addPoolToRuleFunc, deletePoolFromRuleFunc } = useRulePoolListModel(ruleId, bindKey)
  const { stocks: ruleStocks, total: stocksTotal, loading: stocksLoading } = useRuleStockListModel(ruleId, bindKey, selectedPoolId)
  const { pools: allPools, fetchAllPools } = useAllPoolsListModel()
  const { tradings: agentTradings, total: tradingsTotal, loading: tradingsLoading, fetchTradings } = useRuleTradingListModel(ruleId, tradingCurrentPage)

  // Handle pool selection change
  const handlePoolChange = (poolId: number) => {
    setSelectedPoolId(poolId)
  }

  // Initialize all pools list
  useEffect(() => {
    if (ruleId) {
      fetchAllPools()
    }
  }, [ruleId, fetchAllPools])

  // Add pools to rule
  const handleAddPools = async () => {
    try {
      await addPoolToRuleFunc(selectedPoolIds)
      setAddPoolModalVisible(false)
      setSelectedPoolIds([])
    } catch (error) {
      // Error already handled in model
    }
  }

  // Delete pool from rule
  const handleDeletePool = async (poolId: number) => {
    try {
      await deletePoolFromRuleFunc(poolId)
    } catch (error) {
      // Error already handled in model
    }
  }

  // Comparison functions
  const compareEarn: CompareFn<Pool> = (a, b) => {
    const earnA = a.earn ?? MinRate
    const earnB = b.earn ?? MinRate
    return earnA - earnB
  }

  const compareAvgEarn: CompareFn<Pool> = (a, b) => {
    const earnA = a.avg_earn ?? MinRate
    const earnB = b.avg_earn ?? MinRate
    return earnA - earnB
  }

  const compareEarnRate: CompareFn<Pool> = (a, b) => {
    const earnA = a.earning_rate ?? MinRate
    const earnB = b.earning_rate ?? MinRate
    return earnA - earnB
  }

  const compareStockEarn: CompareFn<StockRuleEarn> = (a, b) => {
    const earnA = a.earn ?? MinRate
    const earnB = b.earn ?? MinRate
    return earnA - earnB
  }

  const compareStockAvgEarn: CompareFn<StockRuleEarn> = (a, b) => {
    const earnA = a.avg_earn ?? MinRate
    const earnB = b.avg_earn ?? MinRate
    return earnA - earnB
  }

  // Pools table columns
  const poolColumns = [
    { dataIndex: 'id', title: 'ID', hideInTable: true },
    { dataIndex: 'name', width: '7%', title: 'Name' },
    { dataIndex: 'earn', width: '10%', title: 'Earnings', sorter: compareEarn },
    { dataIndex: 'avg_earn', width: '10%', title: 'Average Earnings', sorter: compareAvgEarn },
    { dataIndex: 'trading_times', width: '7%', title: 'Trading Times' },
    { dataIndex: 'earning_rate', width: '10%', title: 'Earning Rate', sorter: compareEarnRate },
    { dataIndex: 'updated_at', width: '10%', title: 'Updated At', valueType: 'dateTime' as const },
    {
      dataIndex: 'operator',
      title: 'Actions',
      width: '15%',
      render: (_: any, record: Pool) => (
        <Button danger onClick={() => handleDeletePool(record.id)}>
          Delete
        </Button>
      ),
    },
  ]

  // Stocks table columns
  const stockColumns = [
    { dataIndex: 'code', width: '5%', title: 'Code' },
    { dataIndex: 'name', width: '5%', title: 'Name' },
    { dataIndex: 'earn', width: '5%', title: 'Earnings', sorter: compareStockEarn },
    { dataIndex: 'avg_earn', width: '5%', title: 'Average Earnings', sorter: compareStockAvgEarn },
    { dataIndex: 'trading_times', width: '7%', title: 'Trading Times' },
    { dataIndex: 'earning_rate', width: '5%', title: 'Earning Rate' },
    { dataIndex: 'updated_at', width: '7%', title: 'Updated At', valueType: 'dateTime' as const },
  ]

  // Agent Trading table columns
  const tradingColumns = [
    { dataIndex: 'id', width: '5%', title: 'ID' },
    { dataIndex: 'stock', width: '10%', title: 'Stock' },
    { dataIndex: 'trading_date', width: '15%', title: 'Trading Date', valueType: 'dateTime' as const },
    { dataIndex: 'trading_type', width: '10%', title: 'Trading Type' },
    // { dataIndex: 'trading_amount', width: '10%', title: 'Trading Amount' },
    // { dataIndex: 'sims', width: '15%', title: 'Sims' },
    { dataIndex: 'created_at', width: '15%', title: 'Created At', valueType: 'dateTime' as const },
  ]

  // Filter out already added pools
  const availablePools = allPools.filter(
    (pool) => !rulePools.some((rulePool) => rulePool.id === pool.id)
  )

  return (
    <div style={{ padding: '20px' }}>
      <h1>
        {ruleId} {ruleName}
      </h1>

      <Tabs
        activeKey={currentTab}
        onChange={setCurrentTab}
        items={[
          {
            label: 'Pools',
            key: '1',
            children: (
              <Spin spinning={poolsLoading}>
                <ProTable<Pool>
                  dataSource={rulePools}
                  rowKey="id"
                  pagination={{ pageSize: PageSize, total: poolsTotal }}
                  columns={poolColumns}
                  search={false}
                  toolBarRender={() => [
                    <Button key="1" type="primary" onClick={() => setAddPoolModalVisible(true)}>
                      Add Pool
                    </Button>,
                  ]}
                />
                <Modal
                  title="Add Pools to Rule"
                  open={addPoolModalVisible}
                  onOk={handleAddPools}
                  onCancel={() => setAddPoolModalVisible(false)}
                  destroyOnClose
                >
                  <Select
                    mode="multiple"
                    placeholder="Select Pools"
                    style={{ width: '100%' }}
                    value={selectedPoolIds}
                    onChange={(values) => setSelectedPoolIds(values)}
                    options={availablePools.map((pool) => ({
                      value: pool.id,
                      label: pool.name,
                    }))}
                  />
                </Modal>
              </Spin>
            ),
          },
          {
            label: 'Stocks',
            key: '2',
            children: (
              <Spin spinning={stocksLoading}>
                <div style={{ marginBottom: 16 }}>
                  <Select
                    style={{ width: 200 }}
                    placeholder="Select Pool to View Stocks"
                    allowClear
                    value={selectedPoolId}
                    onChange={handlePoolChange}
                    options={rulePools.map((pool) => ({
                      value: pool.id,
                      label: pool.name,
                    }))}
                  />
                </div>
                <ProTable<StockRuleEarn>
                  dataSource={ruleStocks}
                  rowKey="id"
                  pagination={{ pageSize: PageSize, total: stocksTotal }}
                  columns={stockColumns}
                  search={false}
                  headerTitle={selectedPoolId ? rulePools.find(p => p.id === selectedPoolId)?.name : 'All Stocks'}
                />
              </Spin>
            ),
          },
          // {
          //   label: 'Parameters',
          //   key: '3',
          //   children: <div>Parameter charts under development...</div>,
          // },
          {
            label: 'Indicating',
            key: '4',
            children: (
              <Spin spinning={tradingsLoading}>
                <ProTable<RuleTrading>
                  dataSource={agentTradings}
                  rowKey="id"
                  pagination={{
                    pageSize: PageSize,
                    total: tradingsTotal,
                    current: tradingCurrentPage,
                    onChange: (page) => {
                      setTradingCurrentPage(page)
                      fetchTradings(page)
                    },
                  }}
                  columns={tradingColumns}
                  search={false}
                  headerTitle={`Rule Trading Records (Rule ID: ${ruleId})`}
                />
              </Spin>
            ),
          },
        ]}
      />
    </div>
  )
}

export default RuleDetail
