import { useParams, useLocation } from 'react-router-dom'
import type { ProColumns } from '@ant-design/pro-components'
import { ProTable, ProFormSelect } from '@ant-design/pro-components'
import { Button, Divider, Modal, Spin } from 'antd'
import type { ReactNode } from 'react'
import { useState, useEffect } from 'react'
import type { Stock } from '@/types'
import { usePoolStockListModel, useAllStocksListModel, usePoolStockMutations } from '@/models'
import type { CompareFn } from 'antd/es/table/interface'
import { MinDate, MinRate } from '@/pages/Shared/const'

const PageSize = 100

const PoolDetail = () => {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const poolName = (location.state as { name: string })?.name?.toUpperCase() || `Pool ${id}`
  const poolId = parseInt(id || '0')

  const [createModalVisible, setCreateModalVisible] = useState<boolean>(false)
  const [deleteModalVisible, setDeleteModalVisible] = useState<boolean>(false)
  const [currentStock, setCurrentStock] = useState<Stock | undefined>()
  const [formKey, setFormKey] = useState(0)

  // Use models
  const { stocks, total, loading, fetchStocks } = usePoolStockListModel(poolId)
  const { stocks: allStocks, fetchAllStocks } = useAllStocksListModel()
  const { addStockToPool, deleteStockFromPool } = usePoolStockMutations(poolId)

  // Initialize all stocks list
  useEffect(() => {
    if (poolId) {
      fetchAllStocks()
    }
  }, [poolId, fetchAllStocks])

  const operationRender = (_: ReactNode, record: Stock) => {
    return (
      <div>
        <Divider type="vertical" />
        <a onClick={() => handleDeleteStock(record)}>Delete</a>
      </div>
    )
  }

  const handleDeleteStock = (record: Stock) => {
    setCurrentStock(record)
    setDeleteModalVisible(true)
  }

  const deleteStockHandler = async () => {
    if (currentStock?.code) {
      const result = await deleteStockFromPool(currentStock.code)
      if (result.success) {
        fetchStocks({ pool_id: poolId })
        setDeleteModalVisible(false)
      }
    }
  }

  const addStockHandler = async (record: Record<string, any>) => {
    const result = await addStockToPool(record.code)
    if (result.success) {
      fetchStocks({ pool_id: poolId })
      setCreateModalVisible(false)
      setFormKey(prev => prev + 1)
    }
  }

  const handleOpenAddModal = () => {
    setFormKey(prev => prev + 1) // Reset form when opening
    setCreateModalVisible(true)
  }

  const handleCloseAddModal = () => {
    setCreateModalVisible(false)
    setFormKey(prev => prev + 1) // Reset form when closing
  }

  // Search stocks
  const handleStockSearch = (value: string) => {
    fetchStocks({ pool_id: poolId, stock_code: value })
  }

  // Clear search
  const handleClearSearch = () => {
    fetchStocks({ pool_id: poolId })
  }

  // Comparison functions
  const compareUpdateDate: CompareFn<Stock> = (a, b) => {
    const dateA = a.updated_at ?? MinDate
    const dateB = b.updated_at ?? MinDate
    return dateA > dateB ? 1 : -1
  }

  const compareCap: CompareFn<Stock> = (a, b) => {
    const stockA = a.cap ?? MinRate
    const stockB = b.cap ?? MinRate
    return stockA - stockB
  }

  // Filter out stocks already in pool
  const availableStocks = allStocks.filter(
    (stock) => !stocks.some((poolStock) => poolStock.code === stock.code)
  )

  const columns: ProColumns<Stock>[] = [
    {
      dataIndex: 'code',
      width: '7%',
      title: 'Code',
      renderFormItem: () => (
        <ProFormSelect
          showSearch
          placeholder="Search stock code"
          options={stocks.map((item) => ({
            value: item.code,
            label: `${item.code}${item.name}`,
          }))}
          fieldProps={{
            filterOption: (input: string, option?: { label?: string }) => (option?.label ?? '').indexOf(input) >= 0,
            onSelect: (value: string) => handleStockSearch(value),
            onClear: handleClearSearch,
            allowClear: true,
          }}
        />
      ),
    },
    { dataIndex: 'name', width: '7%', title: 'Name', hideInSearch: true },
    { dataIndex: 'pools', width: '20%', title: 'Pools', hideInSearch: true },
    { dataIndex: 'cap', width: '7%', title: 'Market Cap', hideInSearch: true, sorter: compareCap },
    {
      dataIndex: 'updated_at',
      width: '10%',
      title: 'Updated At',
      valueType: 'dateTime' as const,
      hideInSearch: true,
      sorter: compareUpdateDate,
    },
    {
      dataIndex: 'operator',
      title: 'Actions',
      width: '15%',
      hideInSearch: true,
      render: operationRender,
    },
  ]

  const formColumns: ProColumns<Stock>[] = [
    {
      dataIndex: 'code',
      width: '7%',
      title: 'Code',
      renderFormItem: () => (
        <ProFormSelect
          name="code"
          label="Stock"
          showSearch
          placeholder="Select stock to add"
          options={availableStocks.map((item) => ({
            value: item.code,
            label: `${item.code}${item.name}`,
          }))}
          fieldProps={{
            filterOption: (input: string, option?: { label?: string }) => (option?.label ?? '').indexOf(input) >= 0,
          }}
        />
      ),
    },
  ]

  return (
    <div style={{ padding: '20px' }}>
      <Spin tip="Loading..." spinning={loading}>
        <ProTable<Stock>
          headerTitle={poolName}
          dataSource={stocks}
          rowKey="code"
          pagination={{
            showQuickJumper: false,
            pageSize: PageSize,
            total: total,
          }}
          columns={columns}
          search={{
            optionRender: false,
          }}
          dateFormatter="string"
          toolBarRender={() => [
            <Button key="1" type="primary" onClick={handleOpenAddModal}>
              Add
            </Button>,
          ]}
        />
        <Modal
          title="Add to Pool"
          open={createModalVisible}
          onCancel={handleCloseAddModal}
          footer={null}
          destroyOnClose
        >
          <ProTable<Stock, Stock>
            key={formKey}
            onSubmit={addStockHandler}
            rowKey="code"
            type="form"
            columns={formColumns}
          />
        </Modal>
        <Modal
          title="Delete"
          open={deleteModalVisible}
          onOk={deleteStockHandler}
          onCancel={() => setDeleteModalVisible(false)}
        >
          Are you sure you want to delete stock {currentStock?.name} from {poolName}?
        </Modal>
      </Spin>
    </div>
  )
}

export default PoolDetail
