// 导出所有服务
export * from './api'
export { default as websocketService } from './websocket'
export { default as storageService } from './storage'

// 重新导出常用服务
import { apiServices } from './api'
import websocketService from './websocket'
import storageService from './storage'

export const services = {
  api: apiServices,
  websocket: websocketService,
  storage: storageService,
}

export default services