import { Tabs } from 'antd'
import AgentRules from './AgentRules'

export type RLRulesIndexProps = {
  ruleType: string
}

const AgentRulesIndex: React.FC<RLRulesIndexProps> = () => {
  return (
    <>
      <Tabs
        defaultActiveKey="1"
        items={[
          {
            label: 'Earns',
            key: '1',
            children: <AgentRules ruleType="agent"></AgentRules>,
          },
        ]}
      />
    </>
  )
}

export default AgentRulesIndex
