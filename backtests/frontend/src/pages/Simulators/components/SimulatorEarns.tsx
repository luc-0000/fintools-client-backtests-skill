import { ProTable } from '@ant-design/pro-components'
import { Spin } from 'antd'
import { useEffect } from 'react'
import { useTradeEarnListModel } from '@/models'

const SimulatorEarns: React.FC = () => {
  const { tradeEarns, loading, fetchTradeEarns } = useTradeEarnListModel({})

  useEffect(() => {
    fetchTradeEarns({})
  }, [fetchTradeEarns])

  const columns = [
    { dataIndex: 'id', title: 'ID' },
    { dataIndex: 'sim_id', title: 'Simulator ID' },
    { dataIndex: 'cum_earn', title: 'Cumulative Earnings' },
    { dataIndex: 'trading_times', title: 'Trading Times' },
    { dataIndex: 'updated_at', title: 'Updated At', valueType: 'dateTime' },
  ]

  return (
    <Spin spinning={loading}>
      <ProTable
        dataSource={tradeEarns}
        rowKey="id"
        pagination={{ pageSize: 50 }}
        columns={columns}
        search={false}
      />
    </Spin>
  )
}

export default SimulatorEarns
