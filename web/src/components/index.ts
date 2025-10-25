// 导出所有组件
export * from './layout'
export * from './common'

// 重新导出常用组件
import { layoutComponents } from './layout'
import { commonComponents } from './common'

export const components = {
  layout: layoutComponents,
  common: commonComponents,
}

export default components