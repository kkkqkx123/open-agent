// 导出图表组件
export { default as MetricsChart } from './MetricsChart'

// 重新导出常用组件
import MetricsChart from './MetricsChart'

export const chartComponents = {
  MetricsChart,
}

export default chartComponents