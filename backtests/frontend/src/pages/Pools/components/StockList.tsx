import { ProTable, ProForm, ProFormText, ProFormSelect } from '@ant-design/pro-components'
import { Button, Modal, Spin } from 'antd'
import { useState } from 'react'
import type { Stock } from '@/types'
import { useStockListModel } from '@/models'
import { usePoolListModel } from '@/models'

const PageSize = 50

const StockList: React.FC = () => {
  const [addModalVisible, setAddModalVisible] = useState<boolean>(false)
  const [deleteModalVisible, setDeleteModalVisible] = useState<boolean>(false)
  const [currentStock, setCurrentStock] = useState<Stock | undefined>()

  const { stocks, total, loading, addStock, deleteStock } = useStockListModel()
  const { pools } = usePoolListModel()

  const handleDeleteStock = (record: Stock) => {
    setCurrentStock(record)
    setDeleteModalVisible(true)
  }

  const handleAddStock = (record: any) => {
    setAddModalVisible(false)
    addStock(record).catch(console.error)
  }

  const columns = [
    { dataIndex: 'code', width: '10%', title: 'Code' },
    { dataIndex: 'name', width: '10%', title: 'Name' },
    { dataIndex: 'earn', width: '10%', title: 'Earnings' },
    { dataIndex: 'updated_at', width: '15%', title: 'Updated At', valueType: 'dateTime' as const },
    { dataIndex: 'operator', title: 'Actions', render: (_: any, record: Stock) => (
      <a onClick={() => handleDeleteStock(record)}>Delete</a>
    )}
  ]

  return (
    <Spin tip="Loading..." spinning={loading}>
      <ProTable<Stock>
        dataSource={stocks}
        rowKey="code"
        pagination={{ pageSize: PageSize, total }}
        columns={columns}
        search={false}
        toolBarRender={() => [
          <Button key="1" type="primary" onClick={() => setAddModalVisible(true)}>
            Add
          </Button>
        ]}
      />
      <Modal title="Add" open={addModalVisible} onCancel={() => setAddModalVisible(false)} footer={null}>
        <ProForm onFinish={handleAddStock}>
          <ProFormText name="code" label="Code" required />
          <ProFormText name="name" label="Name" required />
          <ProFormSelect
            name="pool_id"
            label="Belonging Pool"
            options={pools.map(p => ({ label: p.name, value: p.id }))}
          />
        </ProForm>
      </Modal>
      <Modal title="Delete" open={deleteModalVisible} onOk={() => { if (currentStock?.code) { deleteStock(currentStock.code) } setDeleteModalVisible(false) }} onCancel={() => setDeleteModalVisible(false)}>
        Are you sure you want to delete stock {currentStock?.name}?
      </Modal>
    </Spin>
  )
}

export default StockList
