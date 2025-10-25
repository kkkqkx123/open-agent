// 导出所有工具函数
export * from './format'
export * from './validation'

// 重新导出常用工具函数
import formatUtils from './format'
import validationUtils from './validation'

export const utils = {
  format: formatUtils,
  validation: validationUtils,
}

export default utils