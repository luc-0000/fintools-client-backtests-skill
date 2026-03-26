import { ProTable } from '@ant-design/pro-components'
import { Spin } from 'antd'
import { useEffect } from 'react'
import { useRuleParamsModel } from '@/models'

const RuleParamList: React.FC = () => {
  const { ruleParams, loading, fetchRuleParams } = useRuleParamsModel({})

  useEffect(() => {
    fetchRuleParams({})
  }, [fetchRuleParams])

  const columns = [
    { dataIndex: 'id', title: 'ID' },
    { dataIndex: 'rule_id', title: 'Rule ID' },
    { dataIndex: 'param_name', title: 'Parameter Name' },
    { dataIndex: 'param_value', title: 'Parameter Value' },
  ]

  return (
    <Spin spinning={loading}>
      <ProTable
        dataSource={ruleParams}
        rowKey="id"
        pagination={{ pageSize: 50 }}
        columns={columns}
        search={false}
      />
    </Spin>
  )
}

export default RuleParamList
