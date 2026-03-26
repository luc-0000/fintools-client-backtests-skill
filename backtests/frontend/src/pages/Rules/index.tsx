import { Tabs, Button, Modal } from 'antd'
import { useEffect, useState } from 'react'
import RuleList from './components/RuleList'

const Rules = () => {
  const [schemaModalVisible, setSchemaModalVisible] = useState(false)

  useEffect(() => {
    document.title = 'Agents'
  }, [])

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h1 style={{ margin: 0 }}>Agents</h1>
        <Button type="link" onClick={() => setSchemaModalVisible(true)}>
          Agent Schema
        </Button>
      </div>
      <Modal
        title="Agent Schema Specification"
        open={schemaModalVisible}
        onCancel={() => setSchemaModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setSchemaModalVisible(false)}>
            Close
          </Button>
        ]}
      >
        <div style={{ fontSize: '14px', lineHeight: '1.8' }}>
          <p><strong>Input:</strong> Stock code (e.g., "600519.SH")</p>
          <p><strong>Output:</strong> Boolean (True/False) indicating whether the stock is "indicating"</p>
          <p><strong>Indicating Definition:</strong> When True, represents a buy signal that will execute before today's market close</p>
          <p><strong>Note:</strong> Sell rules are defined separately in simulators</p>
        </div>
      </Modal>
      <Tabs
        defaultActiveKey="remote"
        items={[
          {
            label: 'Remote Agents',
            key: 'remote',
            children: <RuleList ruleType="remote_agent" />,
          },
        ]}
      />
    </div>
  )
}

export default Rules
