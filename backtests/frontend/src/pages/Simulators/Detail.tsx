import { useParams, useLocation } from 'react-router-dom'
import { Tabs, Spin } from 'antd'
import { useState, useEffect } from 'react'
import { ProTable, ProFormSelect } from '@ant-design/pro-components'
import { useSimulatorLogModel, useSimulatorParamsModel, useSimulatorTradingModel } from '@/models'
import type { SimTrading } from '@/types'
import * as echarts from 'echarts'

const PageSize = 100

const SimulatorDetail = () => {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const state = location.state as { rule_name?: string; rule_id?: number } | undefined
  const ruleName = state?.rule_name?.toUpperCase() || 'UNKNOWN'
  const ruleId = state?.rule_id || 0
  const simId = parseInt(id || '0')

  const [currentTab, setCurrentTab] = useState<string>('1')
  const [chartsInited, setChartsInited] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)

  // Use models
  const { log: simLog, loading: logLoading } = useSimulatorLogModel(simId)
  const { params: earningInfo, loading: earnsLoading } = useSimulatorParamsModel(simId)
  const { trading, total: tradingTotal, loading: tradingLoading, stocks: tradingStocks, fetchTrading: fetchSimulatorTrading } = useSimulatorTradingModel(simId, PageSize)

  // Update charts
  useEffect(() => {
    if (earningInfo && currentTab === '2') {
      // Use setTimeout to ensure DOM is rendered
      const timer = setTimeout(() => {
        updateCharts()
        setChartsInited(true)
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [earningInfo, currentTab])

  // Clean up charts
  useEffect(() => {
    return () => {
      const earnsChartDom = document.getElementById('earnsGraph')
      const earnsCompareChartDom = document.getElementById('earnsCompareGraph')

      if (earnsChartDom) {
        const earnsChart = echarts.getInstanceByDom(earnsChartDom)
        if (earnsChart) {
          earnsChart.dispose()
        }
      }

      if (earnsCompareChartDom) {
        const earnsCompareChart = echarts.getInstanceByDom(earnsCompareChartDom)
        if (earnsCompareChart) {
          earnsCompareChart.dispose()
        }
      }
    }
  }, [])

  const updateCharts = () => {
    console.log('Updating charts with earningInfo:', earningInfo)

    const earnsChartDom = document.getElementById('earnsGraph')
    console.log('earnsChartDom:', earnsChartDom)

    if (earnsChartDom) {
      try {
        const earnsChart = echarts.init(earnsChartDom)
        const earnsOption = getEarnsOption(earningInfo)
        console.log('earnsOption:', earnsOption)
        earnsOption && earnsChart.setOption(earnsOption, false)
      } catch (error) {
        console.error('Failed to initialize earns chart:', error)
      }
    }

    const earnsCompareChartDom = document.getElementById('earnsCompareGraph')
    console.log('earnsCompareChartDom:', earnsCompareChartDom)

    if (earnsCompareChartDom) {
      try {
        const earnsCompareChart = echarts.init(earnsCompareChartDom)
        const earnsCompareOption = getEarnsCompareOption(earningInfo)
        console.log('earnsCompareOption:', earnsCompareOption)
        earnsCompareOption && earnsCompareChart.setOption(earnsCompareOption, false)
      } catch (error) {
        console.error('Failed to initialize earns compare chart:', error)
      }
    }
  }

  const getEarnsOption = (earningInfo: any): echarts.EChartsOption => {
    return {
      xAxis: {
        name: 'Dates',
        type: 'category',
        data: earningInfo.sell_dates || [],
      },
      yAxis: [
        {
          name: 'Earns',
          type: 'value',
        },
        {
          name: 'ER_After',
          type: 'value',
          position: 'right',
        },
        {
          name: 'CE_After',
          type: 'value',
          position: 'left',
          offset: 50,
        },
        {
          name: 'AE_After',
          type: 'value',
          position: 'right',
          offset: 50,
        },
      ],
      tooltip: {
        trigger: 'axis',
      },
      series: [
        {
          name: 'Earns',
          data: earningInfo.earns || [],
          type: 'line',
          markPoint: {
            data: [{ type: 'max', name: 'Max' }, { type: 'min', name: 'Min' }],
          },
        },
        {
          name: 'ERAfter',
          type: 'line',
          yAxisIndex: 1,
          data: earningInfo.earn_rates_after || [],
          smooth: true,
        },
        {
          name: 'CEAfter',
          type: 'line',
          yAxisIndex: 2,
          data: earningInfo.cum_earns_after || [],
          smooth: true,
        },
        {
          name: 'AEAfter',
          type: 'line',
          yAxisIndex: 3,
          data: earningInfo.avg_earns_after || [],
          smooth: true,
        },
      ],
    }
  }

  const getEarnsCompareOption = (earningInfo: any): echarts.EChartsOption => {
    return {
      xAxis: {
        name: 'Dates',
        type: 'category',
        data: earningInfo.bought_dates || [],
      },
      yAxis: [
        {
          name: 'Assets',
          type: 'value',
        },
      ],
      tooltip: {
        trigger: 'axis',
      },
      legend: {
        orient: 'horizontal',
      },
      series: [
        {
          name: 'SnowyTrader',
          data: earningInfo.assets || [],
          type: 'line',
          yAxisIndex: 0,
          markPoint: {
            data: [{ type: 'max', name: 'Max' }, { type: 'min', name: 'Min' }],
          },
        },
        {
          name: 'Index300',
          type: 'line',
          yAxisIndex: 0,
          data: earningInfo.index_close || [],
          smooth: true,
          lineStyle: {
            opacity: 0.8,
            color: '#d62828ff',
          },
          itemStyle: {
            color: '#d62828ff',
          },
        },
      ],
    }
  }

  // Trading table columns
  const tradingColumns = [
    {
      dataIndex: 'trading_date',
      width: '10%',
      title: 'Trading Date',
      valueType: 'dateTime' as const,
      hideInSearch: true,
    },
    {
      dataIndex: 'stock',
      width: '10%',
      title: 'Stock',
      renderFormItem: () => (
        <ProFormSelect
          showSearch
          options={tradingStocks.map((stock) => ({ value: stock, label: stock }))}
          fieldProps={{
            filterOption: (input: string, option?: { label?: string }) => (option?.label ?? '').indexOf(input) >= 0,
            onSelect: (value: string) => fetchSimulatorTrading(1, { stock: value }),
            onClear: () => fetchSimulatorTrading(),
            allowClear: true,
          }}
        />
      ),
    },
    { dataIndex: 'stock_name', width: '10%', title: 'Stock Name', hideInSearch: true },
    { dataIndex: 'trading_type', width: '10%', title: 'Trading Type', hideInSearch: true },
    { dataIndex: 'trading_amount', width: '10%', title: 'Trading Amount', hideInSearch: true },
  ]

  return (
    <div style={{ padding: '20px' }}>
      <h1>
        Simulator {simId} - {ruleName}
      </h1>
      <p>Rule ID: {ruleId}</p>

      <Tabs
        activeKey={currentTab}
        onChange={(key) => {
          setCurrentTab(key)
          if (key === '2' && !chartsInited && earningInfo) {
            // Initialize charts when switching to Earns Tab
            setTimeout(() => {
              updateCharts()
              setChartsInited(true)
            }, 100)
          }
        }}
        items={[
          {
            label: 'Logs',
            key: '1',
            children: (
              <Spin spinning={logLoading}>
                <div
                  dangerouslySetInnerHTML={{
                    __html: simLog || 'No logs available',
                  }}
                />
              </Spin>
            ),
          },
          {
            label: 'Earns',
            key: '2',
            children: (
              <Spin spinning={earnsLoading}>
                <div>
                  <h3>Earns V.S. Dates</h3>
                  <div
                    id="earnsGraph"
                    style={{ width: '100%', height: '400px' }}
                  />
                  <p></p>
                  <h3>Earns V.S. Index300</h3>
                  <div
                    id="earnsCompareGraph"
                    style={{ width: '100%', height: '400px' }}
                  />
                </div>
              </Spin>
            ),
          },
          {
            label: 'Trading',
            key: '3',
            children: (
              <Spin spinning={tradingLoading}>
                <ProTable<SimTrading>
                  dataSource={trading}
                  rowKey="id"
                  pagination={{
                    showQuickJumper: false,
                    pageSize: PageSize,
                    total: tradingTotal,
                    current: currentPage,
                    onChange: (page) => {
                      setCurrentPage(page)
                      fetchSimulatorTrading(page)
                    },
                  }}
                  columns={tradingColumns}
                  search={{
                    optionRender: false,
                  }}
                  toolBarRender={() => []}
                  dateFormatter="string"
                />
              </Spin>
            ),
          },
        ]}
      />
    </div>
  )
}

export default SimulatorDetail
