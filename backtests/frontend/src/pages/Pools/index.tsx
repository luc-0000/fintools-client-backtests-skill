import { Tabs } from 'antd'
import PoolList from './components/PoolList'
import StockList from './components/StockList'

const Pools = () => {
  return (
    <div style={{ padding: '20px' }}>
      <h1>Pools</h1>
      <Tabs
        defaultActiveKey="1"
        items={[
          {
            label: 'Pools',
            key: '1',
            children: <PoolList />,
          },
          {
            label: 'Stocks',
            key: '2',
            children: <StockList />,
          },
        ]}
      />
    </div>
  )
}

export default Pools
