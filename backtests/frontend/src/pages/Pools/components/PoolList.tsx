import { Link } from 'react-router-dom'
import type { ProColumns } from '@ant-design/pro-components'
import {
  ProForm,
  ProFormText,
  ProTable,
} from '@ant-design/pro-components'
import { Button, Divider, Modal, Spin } from 'antd'
import type { ReactNode } from 'react'
import { useState } from 'react'
import type { Pool } from '@/types'
import { usePoolListModel } from '@/models'
import { Messages } from '@/pages/Shared/messages'
import PopupForm from '@/components/PopupForm'

const PageSize = 50

const PoolList: React.FC = () => {
  const [createModalVisible, setCreateModalVisible] = useState<boolean>(false)
  const [updateModalVisible, setUpdateModalVisible] = useState<boolean>(false)
  const [deleteModalVisible, setDeleteModalVisible] = useState<boolean>(false)
  const [currentPool, setCurrentPool] = useState<Pool>({ id: -1, name: '' })

  const { pools, total, loading, addPool, deletePool, updatePool } = usePoolListModel()

  const operationRender = (_: ReactNode, record: Pool) => {
    return (
      <div>
        <a onClick={() => { setUpdateModalVisible(true); setCurrentPool(record) }}>
          {Messages.operationEdit}
        </a>
        <Divider type="vertical" />
        <a onClick={() => handleDeleteCategory(record)}>{Messages.operationDelete}</a>
      </div>
    )
  }

  const nameRender = (_: ReactNode, record: Pool) => {
    return <Link to={`/pool/${record.id}`} state={{ name: record.name }}>{record.name}</Link>
  }

  const handleDeleteCategory = (record: Pool) => {
    setCurrentPool(record)
    setDeleteModalVisible(true)
  }

  const createCategory = (record: Pool) => {
    setCreateModalVisible(false)
    addPool(record).catch(console.error)
  }

  const deleteCategory = () => {
    setDeleteModalVisible(false)
    deletePool(currentPool.id).catch(console.error)
  }

  const updateCategory = (record: Record<string, any>) => {
    setUpdateModalVisible(false)
    updatePool(currentPool.id, { name: record.name }).catch(console.error)
  }

  const columns: ProColumns<Pool>[] = [
    { dataIndex: 'id', width: '3%', title: 'ID', hideInForm: true },
    { dataIndex: 'name', width: '10%', title: 'Name', render: nameRender },
    { dataIndex: 'stocks', width: '10%', title: 'Stock Count', hideInForm: true },
    { dataIndex: 'latest_date', width: '10%', title: 'Latest Date', valueType: 'dateTime', hideInForm: true },
    { dataIndex: 'operator', title: 'Actions', width: '15%', hideInForm: true, render: operationRender }
  ]

  return (
    <Spin tip="Loading..." spinning={loading}>
      <div>
        <ProTable<Pool>
          dataSource={pools}
          rowKey="id"
          pagination={{ pageSize: PageSize, total }}
          columns={columns}
          search={false}
          toolBarRender={() => [
            <Button key="1" type="primary" onClick={() => setCreateModalVisible(true)}>
              Create
            </Button>
          ]}
        />
        <PopupForm
          onCancel={() => setCreateModalVisible(false)}
          modalVisible={createModalVisible}
          formTitle="Create"
        >
          <ProTable<Pool, Pool> onSubmit={createCategory} rowKey="id" type="form" columns={columns} />
        </PopupForm>
        <Modal title="Delete" open={deleteModalVisible} onOk={deleteCategory} onCancel={() => setDeleteModalVisible(false)}>
          Are you sure you want to delete this pool?
        </Modal>
        <PopupForm
          onCancel={() => setUpdateModalVisible(false)}
          modalVisible={updateModalVisible}
          formTitle="Edit"
        >
          <ProForm onFinish={async (values) => updateCategory(values)}>
            <ProFormText width="md" name="name" label="Name" initialValue={currentPool.name} />
          </ProForm>
        </PopupForm>
      </div>
    </Spin>
  )
}

export default PoolList
