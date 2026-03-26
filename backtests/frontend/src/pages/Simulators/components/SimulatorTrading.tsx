import { ProTable } from '@ant-design/pro-components'
import { Spin } from 'antd'
import { useEffect } from 'react'
import { useTradingListModel } from '@/models'

const SimulatorTrading: React.FC = () => {
  const { tradings, loading, fetchTradings } = useTradingListModel({})

  useEffect(() => {
    fetchTradings({})
  }, [fetchTradings])

  const columns = [
    { dataIndex: 'id', title: 'ID' },
    { dataIndex: 'sim_id', title: 'Simulator ID' },
    { dataIndex: 'stock', title: 'Stock' },
    { dataIndex: 'trading_type', title: 'Trading Type' },
    { dataIndex: 'trading_date', title: 'Trading Date', valueType: 'date' },
    { dataIndex: 'trading_amount', title: 'Trading Amount' },
  ]

  return (
    <Spin spinning={loading}>
      <ProTable
        dataSource={tradings}
        rowKey="id"
        pagination={{ pageSize: 50 }}
        columns={columns}
        search={false}
      />
    </Spin>
  )
}

export default SimulatorTrading
