import React from 'react'
import { Empty } from 'antd'
import ReactECharts from 'echarts-for-react'

interface MetricsChartProps {
  data: any[]
  height: number
  type: 'performance' | 'cost' | 'usage' | 'errors'
  title?: string
}

const MetricsChart: React.FC<MetricsChartProps> = ({
  data,
  height,
  type,
  title,
}) => {
  // 生成模拟数据
  const generateMockData = () => {
    const now = Date.now()
    const points = []
    
    for (let i = 23; i >= 0; i--) {
      const timestamp = now - i * 60 * 60 * 1000 // 每小时一个点
      points.push({
        timestamp,
        value: Math.floor(Math.random() * 100) + 50,
        cost: Math.random() * 10 + 5,
        requests: Math.floor(Math.random() * 1000) + 500,
        errors: Math.floor(Math.random() * 10),
        successRate: 95 + Math.random() * 5,
      })
    }
    
    return points
  }

  const chartData = data.length > 0 ? data : generateMockData()

  // 获取图表配置
  const getChartOption = () => {
    const baseOption = {
      grid: {
        top: 40,
        right: 40,
        bottom: 40,
        left: 60,
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: (params: any) => {
          const data = params[0]
          const date = new Date(data.axisValue)
          return `
            <div>
              <div>${date.toLocaleString()}</div>
              <div>${data.seriesName}: ${data.value}</div>
            </div>
          `
        },
      },
      xAxis: {
        type: 'time',
        data: chartData.map(item => item.timestamp),
        axisLabel: {
          formatter: (value: number) => {
            const date = new Date(value)
            return `${date.getHours()}:00`
          },
        },
      },
      yAxis: {
        type: 'value',
        splitLine: {
          lineStyle: {
            color: '#f0f0f0',
          },
        },
      },
    }

    switch (type) {
      case 'performance':
        return {
          ...baseOption,
          title: {
            text: title || '性能趋势',
            left: 'center',
          },
          legend: {
            data: ['响应时间', '成功率'],
            bottom: 0,
          },
          series: [
            {
              name: '响应时间',
              type: 'line',
              data: chartData.map(item => item.value),
              smooth: true,
              lineStyle: {
                color: '#1890ff',
                width: 2,
              },
              itemStyle: {
                color: '#1890ff',
              },
              areaStyle: {
                color: {
                  type: 'linear',
                  x: 0,
                  y: 0,
                  x2: 0,
                  y2: 1,
                  colorStops: [
                    { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
                    { offset: 1, color: 'rgba(24, 144, 255, 0.1)' },
                  ],
                },
              },
            },
            {
              name: '成功率',
              type: 'line',
              data: chartData.map(item => item.successRate),
              smooth: true,
              lineStyle: {
                color: '#52c41a',
                width: 2,
              },
              itemStyle: {
                color: '#52c41a',
              },
            },
          ],
        }

      case 'cost':
        return {
          ...baseOption,
          title: {
            text: title || '成本分析',
            left: 'center',
          },
          legend: {
            data: ['成本', '请求数'],
            bottom: 0,
          },
          series: [
            {
              name: '成本',
              type: 'bar',
              data: chartData.map(item => item.cost),
              itemStyle: {
                color: '#faad14',
              },
            },
            {
              name: '请求数',
              type: 'line',
              data: chartData.map(item => item.requests / 100),
              smooth: true,
              lineStyle: {
                color: '#722ed1',
                width: 2,
              },
              itemStyle: {
                color: '#722ed1',
              },
            },
          ],
        }

      case 'usage':
        return {
          ...baseOption,
          title: {
            text: title || '使用情况',
            left: 'center',
          },
          legend: {
            data: ['请求数', '错误数'],
            bottom: 0,
          },
          series: [
            {
              name: '请求数',
              type: 'line',
              data: chartData.map(item => item.requests),
              smooth: true,
              lineStyle: {
                color: '#1890ff',
                width: 2,
              },
              itemStyle: {
                color: '#1890ff',
              },
              areaStyle: {
                color: {
                  type: 'linear',
                  x: 0,
                  y: 0,
                  x2: 0,
                  y2: 1,
                  colorStops: [
                    { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
                    { offset: 1, color: 'rgba(24, 144, 255, 0.1)' },
                  ],
                },
              },
            },
            {
              name: '错误数',
              type: 'line',
              data: chartData.map(item => item.errors),
              smooth: true,
              lineStyle: {
                color: '#ff4d4f',
                width: 2,
              },
              itemStyle: {
                color: '#ff4d4f',
              },
            },
          ],
        }

      case 'errors':
        return {
          ...baseOption,
          title: {
            text: title || '错误趋势',
            left: 'center',
          },
          legend: {
            data: ['错误数'],
            bottom: 0,
          },
          series: [
            {
              name: '错误数',
              type: 'bar',
              data: chartData.map(item => item.errors),
              itemStyle: {
                color: '#ff4d4f',
              },
            },
          ],
        }

      default:
        return baseOption
    }
  }

  // 如果没有数据，显示空状态
  if (chartData.length === 0) {
    return (
      <div style={{ height }}>
        <Empty description="暂无数据" />
      </div>
    )
  }

  return (
    <div className="metrics-chart">
      <ReactECharts
        option={getChartOption()}
        style={{ height }}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  )
}

export default MetricsChart