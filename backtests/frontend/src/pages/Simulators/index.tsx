import { Tabs, Button, Modal, InputNumber, message, Spin } from 'antd'
import { useState, useEffect } from 'react'
import SimulatorAgent from './components/SimulatorAgent'
import { simulatorConfigService } from '@/services'

const Simulators = () => {
  const [instructionModalVisible, setInstructionModalVisible] = useState(false)
  const [configModalVisible, setConfigModalVisible] = useState(false)
  const [configLoading, setConfigLoading] = useState(false)
  const [configSaving, setConfigSaving] = useState(false)
  const [sellConfig, setSellConfig] = useState({
    profit_threshold: 0,
    stop_loss: 5,
    max_holding_days: 5
  })
  const [tempConfig, setTempConfig] = useState({ ...sellConfig })

  // Fetch config on mount
  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    setConfigLoading(true)
    try {
      const response = await simulatorConfigService.getConfig() as any
      if (response.code === 'SUCCESS') {
        setSellConfig(response.data)
        setTempConfig(response.data)
      }
    } catch (error) {
      console.error('Failed to fetch config:', error)
    } finally {
      setConfigLoading(false)
    }
  }

  const handleSaveConfig = async () => {
    setConfigSaving(true)
    try {
      const response = await simulatorConfigService.updateConfig(tempConfig) as any
      if (response.code === 'SUCCESS') {
        setSellConfig(response.data)
        message.success('Configuration updated successfully!')
        setConfigModalVisible(false)
      } else {
        message.error('Failed to update configuration')
      }
    } catch (error) {
      message.error('Failed to update configuration')
      console.error('Error updating config:', error)
    } finally {
      setConfigSaving(false)
    }
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h1 style={{ margin: 0 }}>Simulators</h1>
        <div>
          <Button onClick={() => setConfigModalVisible(true)} style={{ marginRight: '8px' }}>
            Config
          </Button>
          <Button type="link" onClick={() => setInstructionModalVisible(true)}>
            Trading Mechanism
          </Button>
        </div>
      </div>

      {/* Global Sell Configuration Display */}
      <Spin spinning={configLoading}>
        <div style={{
          padding: '12px 16px',
          marginBottom: '16px',
          backgroundColor: '#1f1f1f',
          borderRadius: '6px',
          color: '#fff'
        }}>
          <div style={{ display: 'flex', gap: '24px', fontSize: '14px', alignItems: 'center' }}>
            <span style={{ color: '#fff' }}><strong>Global Sell Conditions:</strong></span>
            <span style={{ color: '#d9d9d9' }}>Profit Threshold: <strong style={{ color: '#52c41a' }}>{sellConfig.profit_threshold}%</strong></span>
            <span style={{ color: '#d9d9d9' }}>Stop Loss: <strong style={{ color: '#ff4d4f' }}>{sellConfig.stop_loss}%</strong></span>
            <span style={{ color: '#d9d9d9' }}>Max Holding Days: <strong style={{ color: '#1890ff' }}>{sellConfig.max_holding_days} days</strong></span>
          </div>
        </div>
      </Spin>

      {/* Config Edit Modal */}
      <Modal
        title="Edit Global Sell Conditions"
        open={configModalVisible}
        onCancel={() => {
          setConfigModalVisible(false)
          setTempConfig({ ...sellConfig })
        }}
        onOk={handleSaveConfig}
        confirmLoading={configSaving}
        width={500}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px' }}>Profit Threshold (%):</label>
            <InputNumber
              min={0}
              max={100}
              step={0.1}
              value={tempConfig.profit_threshold}
              onChange={(value) => setTempConfig({ ...tempConfig, profit_threshold: value || 0 })}
              style={{ width: '100%' }}
            />
            <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>
              Sell when profit &ge; this value (0 = sell when price &gt; buy price)
            </div>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px' }}>Stop Loss (%):</label>
            <InputNumber
              min={0}
              max={100}
              step={0.5}
              value={tempConfig.stop_loss}
              onChange={(value) => setTempConfig({ ...tempConfig, stop_loss: value || 0 })}
              style={{ width: '100%' }}
            />
            <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>
              Sell when loss percent &ge; this value
            </div>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px' }}>Max Holding Days:</label>
            <InputNumber
              min={1}
              max={30}
              step={1}
              value={tempConfig.max_holding_days}
              onChange={(value) => setTempConfig({ ...tempConfig, max_holding_days: value || 1 })}
              style={{ width: '100%' }}
            />
            <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>
              Maximum trading days before forced sell
            </div>
          </div>
        </div>
      </Modal>

      <Modal
        title="Agent Simulator Trading Mechanism"
        open={instructionModalVisible}
        onCancel={() => setInstructionModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setInstructionModalVisible(false)}>
            Close
          </Button>
        ]}
      >
        <div style={{ fontSize: '14px', lineHeight: '1.8' }}>
          <p><strong>Buy Signal (Indicating):</strong> Generated by agent analysis in Rules, stored in agent_trading table</p>
          <p><strong>Buy Execution:</strong> On the next trading day after indicating, buy at close price (unless price increases &ge;9.5%)</p>
          <p><strong>Global Sell Conditions:</strong> (configured via Config button) Position is sold when ANY of the following is met:</p>
          <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
            <li><strong>Profit:</strong> (sell_price - buy_price) / buy_price &ge; profit_threshold%</li>
            <li><strong>Stop Loss:</strong> Loss percent &ge; stop_loss%</li>
            <li><strong>Time Exit:</strong> After max_holding_days trading days</li>
          </ul>
          <p><strong>Failed Sell:</strong> Cannot sell when daily change &le; -9.5% (limit down)</p>
          <p><strong>Position Size:</strong> Fixed amount per stock (INIT_MONEY_PER_STOCK)</p>
        </div>
      </Modal>
      <Tabs
        defaultActiveKey="remote"
        items={[
          {
            label: 'Remote Agents',
            key: 'remote',
            children: <SimulatorAgent ruleType="remote_agent" />,
          },
        ]}
      />
    </div>
  )
}

export default Simulators
