import {
  ProForm,
  ProFormText,
  ProTable,
} from '@ant-design/pro-components'
import type { ReactNode } from 'react'
import { useState } from 'react'
import type { Rule } from '@/types'
import { Link } from 'react-router-dom'
import { Button, Divider, Modal, Spin } from 'antd'
import { MinRate } from '@/pages/Shared/const'
import { Messages } from '@/pages/Shared/messages'
import { useRuleListModel } from '@/models'
import PopupForm from '@/components/PopupForm'
import type { CompareFn } from 'antd/es/table/interface'

const PageSize = 50

export type AgentRulesProps = {
  ruleType: string
}

const AgentRules: React.FC<AgentRulesProps> = ({ ruleType }: AgentRulesProps) => {
  const [deleteModalVisible, setDeleteModalVisible] = useState<boolean>(false)
  const [currentRule, setCurrentRule] = useState<Rule>()
  const [editModalVisible, setEditModalVisible] = useState<boolean>(false)

  const { rules, total, loading, deleteRuleFunc, editRuleFunc } = useRuleListModel({ rule_type: ruleType })

  // Render function
  const nameRender = (_: ReactNode, record: Rule) => {
    const path = `/rule/${record.id}`
    const state = { name: record.name, ruleType }
    return (
      <Link
        to={path}
        state={state}
      >
        {record.name}
      </Link>
    )
  }

  const operationRender = (_: ReactNode, record: Rule) => {
    return (
      <div>
        <Button
          onClick={() => {
            // handleUpdateRule(record)
          }}
        >
          Update
        </Button>
        <Divider type="vertical" />
        <Button
          onClick={() => {
            setEditModalVisible(true)
            setCurrentRule(record)
          }}
        >
          {Messages.operationEdit}
        </Button>
        <Divider type="vertical" />
        <Button onClick={() => handleDeleteRule(record)}>{Messages.operationDelete}</Button>
      </div>
    )
  }

  // Handler functions
  const handleDeleteRule = (record: Rule) => {
    setCurrentRule(record)
    setDeleteModalVisible(true)
  }

  const deleteRuleHandler = () => {
    setDeleteModalVisible(false)
    deleteRuleFunc(currentRule?.id || -1)
  }

  const editRuleHandler = (record: Record<string, any>) => {
    setEditModalVisible(false)
    editRuleFunc(currentRule?.id || -1, {
      name: record.name,
      description: record.description,
      func: record.func,
    })
  }

  // Comparison functions
  const compareRuleID: CompareFn<Rule> = (a, b) => {
    const ruleA = a.id ?? MinRate
    const ruleB = b.id ?? MinRate
    return ruleA - ruleB
  }

  const compareRuleName: CompareFn<Rule> = (a, b) => {
    const ruleA = a.name ?? ''
    const ruleB = b.name ?? ''
    if (ruleA > ruleB) return 1
    else return -1
  }

  const columns = [
    {
      dataIndex: 'id',
      width: '2%',
      title: Messages.ruleId,
      sorter: compareRuleID,
      fixed: 'left' as const,
    },
    {
      dataIndex: 'name',
      width: '3%',
      title: Messages.ruleName,
      render: nameRender,
      sorter: compareRuleName,
    },
    { dataIndex: 'func', width: '4%', title: Messages.agentSims },
    { dataIndex: 'pools', width: '5%', title: 'Pools' },
    { dataIndex: 'description', width: '3%', title: Messages.agentDescription },
    {
      dataIndex: 'updated_at',
      width: '5%',
      title: Messages.ruleUpdatedAt,
      valueType: 'dateTime' as const,
    },
    {
      dataIndex: 'operator',
      title: Messages.operationTitle,
      width: '10%',
      hideInForm: true,
      render: operationRender,
    },
  ]

  return (
    <Spin tip="Loading..." spinning={loading}>
      <div>
        <ProTable<Rule>
          scroll={{ x: 1800, y: 600 }}
          dataSource={rules}
          rowKey="id"
          pagination={{
            showQuickJumper: false,
            pageSize: PageSize,
            total: total,
          }}
          columns={columns}
          search={false}
          dateFormatter="string"
          toolBarRender={() => []}
        />
        <Modal
          title={Messages.operationDelete}
          open={deleteModalVisible}
          onOk={deleteRuleHandler}
          onCancel={() => setDeleteModalVisible(false)}
        >
          {'Deleting rule: ' + currentRule?.id + '?'}
          <div></div>
          {Messages.deleteWarning}
        </Modal>
        <PopupForm
          onCancel={() => setEditModalVisible(false)}
          modalVisible={editModalVisible}
          formTitle={Messages.operationEdit}
        >
          <ProForm
            submitter={{
              render: (_props, doms) => {
                return [...doms]
              },
            }}
            onFinish={async (values) => {
              editRuleHandler(values)
            }}
          >
            <ProFormText width="md" name="name" label="Name" initialValue={currentRule?.name} />
            <ProFormText
              width="md"
              name="description"
              label="Description"
              initialValue={currentRule?.description}
            />
            <ProFormText width="md" name="func" label="sims" initialValue={currentRule?.func} />
          </ProForm>
        </PopupForm>
      </div>
    </Spin>
  )
}

export default AgentRules
