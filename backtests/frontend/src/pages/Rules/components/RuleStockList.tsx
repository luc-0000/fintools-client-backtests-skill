import { ProTable } from '@ant-design/pro-components'
import { Spin } from 'antd'
import { useEffect } from 'react'
import { useRuleStockModel } from '@/models'

const RuleStockList: React.FC = () => {
  const { ruleStocks, loading, fetchRuleStocks } = useRuleStockModel({})

  useEffect(() => {
    fetchRuleStocks({})
  }, [fetchRuleStocks])

  const columns = [
    { dataIndex: 'stock_code', title: 'Stock Code' },
    { dataIndex: 'stock_name', title: 'Stock Name' },
    { dataIndex: 'rule_id', title: 'Rule ID' },
    { dataIndex: 'earn', title: 'Earnings' },
    { dataIndex: 'earning_rate', title: 'Earning Rate' },
  ]

  return (
    <Spin spinning={loading}>
      <ProTable
        dataSource={ruleStocks}
        rowKey="id"
        pagination={{ pageSize: 50 }}
        columns={columns}
        search={false}
      />
    </Spin>
  )
}

export default RuleStockList
