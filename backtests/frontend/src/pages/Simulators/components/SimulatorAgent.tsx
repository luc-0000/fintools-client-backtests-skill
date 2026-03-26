import { Link } from 'react-router-dom'
import { ProTable } from '@ant-design/pro-components'
import { Button, Modal, Spin, Select, DatePicker } from 'antd'
import { useState } from 'react'
import type { Simulator } from '@/types'
import { useSimulatorListModel, useRuleListModel, useStockListModel } from '@/models'
import PopupForm from '@/components/PopupForm'

type SimulatorAgentProps = {
  ruleType: 'remote_agent'
}

const SimulatorAgent: React.FC<SimulatorAgentProps> = ({ ruleType }) => {
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [deleteModalVisible, setDeleteModalVisible] = useState(false)
  const [currentSim, setCurrentSim] = useState<Simulator | undefined>()

  const { simulators, total, loading, running, addSimulatorFunc, deleteSimulatorFunc, runSimulator } = useSimulatorListModel({ rule_type: ruleType })
  const { rules: rulesData } = useRuleListModel({ rule_type: ruleType })
  const { stocks: stocksData } = useStockListModel({})

  // Custom form render function
  const createForm = (item: any) => {
    if (item.dataIndex === 'rule_id') {
      const options = rulesData.map((rule) => ({
        value: rule.id,
        label: `${rule.id}-${rule.name}`,
      }))
      return <Select options={options} showSearch style={{ width: '100%' }} />
    }

    if (item.dataIndex === 'init_money') {
      const options = [
        { value: 10000, label: '10000' },
        { value: 50000, label: '50000' },
        { value: 100000, label: '100000' },
      ]
      return <Select options={options} style={{ width: '100%' }} />
    }

    if (item.dataIndex === 'stock_code') {
      const options = stocksData.map((stock) => ({
        value: stock.code,
        label: stock.name,
      }))
      return <Select options={options} showSearch allowClear style={{ width: '100%' }} />
    }

    if (item.dataIndex === 'start_date') {
      return <DatePicker format="YYYY-MM-DD" style={{ width: '100%' }} />
    }

    return null
  }

  const handleCreateSimulator = async (values: any) => {
    try {
      await addSimulatorFunc(values)
      setCreateModalVisible(false)
    } catch (error) {
      // Error already handled in model
    }
  }

  const columns = [
    {
      dataIndex: 'id',
      width: '3%',
      title: 'ID',
      hideInForm: true,
      render: (_: any, record: Simulator) => (
        <Link to={`/simulator/${record.id}`} state={{ rule_name: record.rule_name, rule_id: record.rule_id }}>
          {record.id}
        </Link>
      ),
    },
    {
      dataIndex: 'rule_name',
      width: '4%',
      title: 'Rule Name',
      hideInForm: true,
      render: (_: any, record: Simulator) => (
        <Link to={`/simulator/${record.id}`} state={{ rule_name: record.rule_name, rule_id: record.rule_id }}>
          {record.rule_name}
        </Link>
      ),
    },
    {
      dataIndex: 'rule_id',
      width: '2%',
      title: 'Rule ID',
      renderFormItem: createForm,
      formItemProps: {
        rules: [{ required: true, message: 'Please select rule' }],
      },
    },
    { dataIndex: 'status', width: '4%', title: 'Status', hideInForm: true },
    {
      dataIndex: 'start_date',
      width: '4%',
      title: 'Start Date',
      valueType: 'date' as const,
      renderFormItem: createForm,
      transform: (value: any) => {
        // Convert Day.js object to YYYY-MM-DD string for backend
        return value && typeof value.format === 'function' ? value.format('YYYY-MM-DD') : value
      },
      formItemProps: {
        rules: [{ required: true, message: 'Please select start date' }],
      },
    },
    { dataIndex: 'first_trade_date', width: '5%', title: 'First Trade Date', hideInForm: true, valueType: 'date' as const },
    {
      dataIndex: 'init_money',
      width: '3%',
      title: 'Init Money',
      renderFormItem: createForm,
      initialValue: 100000,
    },
    { dataIndex: 'current_money', width: '4%', title: 'Current Money', hideInForm: true },
    { dataIndex: 'current_shares', width: '10%', title: 'Holding Shares', hideInForm: true },
    { dataIndex: 'cum_earn', width: '4%', title: 'Cum Earn', hideInForm: true },
    { dataIndex: 'annual_earn', width: '4%', title: 'Annual Earn', hideInForm: true },
    { dataIndex: 'avg_earn', width: '4%', title: 'Avg Earn', hideInForm: true },
    { dataIndex: 'earning_rate', width: '4%', title: 'Earn Rate', hideInForm: true },
    { dataIndex: 'trading_times', width: '4%', title: 'Trading Times', hideInForm: true },
    { dataIndex: 'max_drawback', width: '3%', title: 'Max Drawback', hideInForm: true },
    { dataIndex: 'sharpe', width: '3%', title: 'Sharpe', hideInForm: true },
    { dataIndex: 'indicating_date', width: '4%', title: 'Indicating Date', hideInForm: true, valueType: 'date' as const },
    { dataIndex: 'updated_at', width: '4%', title: 'Updated At', hideInForm: true, valueType: 'dateTime' as const },
    {
      dataIndex: 'operator',
      title: 'Actions',
      width: '6%',
      hideInForm: true,
      render: (_: any, record: Simulator) => (
        <>
          <a onClick={() => { if (record.id) { runSimulator(record.id) } }}>
            {running === record.id ? <Spin size="small" /> : 'Run'}
          </a>
          {' | '}
          <a onClick={() => { setCurrentSim(record); setDeleteModalVisible(true) }}>Delete</a>
        </>
      ),
    },
  ]

  return (
    <Spin spinning={loading}>
      <ProTable<Simulator>
        dataSource={simulators}
        rowKey="id"
        pagination={{ pageSize: 50, total }}
        columns={columns}
        search={false}
        scroll={{ x: 2500, y: 800 }}
        toolBarRender={() => [
          <Button key="1" type="primary" onClick={() => setCreateModalVisible(true)}>
            Create
          </Button>
        ]}
      />
      <PopupForm
        onCancel={() => setCreateModalVisible(false)}
        modalVisible={createModalVisible}
        formTitle="Create Simulator"
      >
        <ProTable
          onSubmit={handleCreateSimulator}
          rowKey="id"
          type="form"
          columns={columns}
          dateFormatter="string"
        />
      </PopupForm>
      <Modal
        title="Delete"
        open={deleteModalVisible}
        onOk={() => { if (currentSim?.id) { deleteSimulatorFunc(currentSim.id) } setDeleteModalVisible(false) }}
        onCancel={() => setDeleteModalVisible(false)}
      >
        Are you sure you want to delete simulator {currentSim?.id}?
      </Modal>
    </Spin>
  )
}

export default SimulatorAgent
