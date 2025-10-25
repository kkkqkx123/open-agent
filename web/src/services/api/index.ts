// 导出所有API服务
export { default as sessionService } from './session'
export { default as workflowService } from './workflow'
export { default as analyticsService } from './analytics'
export { BaseService } from './base'

// 重新导出常用服务
import sessionService from './session'
import workflowService from './workflow'
import analyticsService from './analytics'

export const apiServices = {
  session: sessionService,
  workflow: workflowService,
  analytics: analyticsService,
}

export default apiServices