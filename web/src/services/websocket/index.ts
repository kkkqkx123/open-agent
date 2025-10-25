import { io, Socket } from 'socket.io-client'
import { message } from 'antd'

interface WebSocketServiceConfig {
  url: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
  timeout?: number
}

interface WebSocketEvent {
  event: string
  data: any
  timestamp: number
}

class WebSocketService {
  private socket: Socket | null = null
  private config: WebSocketServiceConfig
  private reconnectAttempts = 0
  private eventHandlers = new Map<string, Function[]>()
  private isConnecting = false
  private connectionPromise: Promise<boolean> | null = null

  constructor(config: WebSocketServiceConfig) {
    this.config = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 5,
      timeout: 10000,
      ...config,
    }
  }

  // 连接WebSocket
  async connect(): Promise<boolean> {
    if (this.socket?.connected) {
      return true
    }

    if (this.isConnecting) {
      return this.connectionPromise || Promise.resolve(false)
    }

    this.isConnecting = true
    this.connectionPromise = new Promise((resolve) => {
      this.socket = io(this.config.url, {
        transports: ['websocket'],
        reconnection: false, // 手动处理重连
        timeout: this.config.timeout,
      })

      this.setupEventListeners(resolve)
    })

    try {
      const result = await this.connectionPromise
      this.isConnecting = false
      this.connectionPromise = null
      return result
    } catch (error) {
      this.isConnecting = false
      this.connectionPromise = null
      return false
    }
  }

  // 断开连接
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.reconnectAttempts = 0
    this.isConnecting = false
    this.connectionPromise = null
  }

  // 设置事件监听器
  private setupEventListeners(resolve: (value: boolean) => void) {
    if (!this.socket) return

    const timeout = setTimeout(() => {
      resolve(false)
      this.handleConnectionError(new Error('连接超时'))
    }, this.config.timeout)

    this.socket.on('connect', () => {
      clearTimeout(timeout)
      console.log('WebSocket连接成功')
      this.reconnectAttempts = 0
      message.success('实时连接已建立')
      this.emit('connected', { timestamp: Date.now() })
      resolve(true)
    })

    this.socket.on('disconnect', (reason) => {
      clearTimeout(timeout)
      console.log('WebSocket连接断开:', reason)
      message.warning('实时连接已断开')
      this.emit('disconnected', { reason, timestamp: Date.now() })
      this.handleReconnect()
    })

    this.socket.on('error', (error) => {
      clearTimeout(timeout)
      console.error('WebSocket连接错误:', error)
      message.error('实时连接出错')
      this.handleConnectionError(error)
      resolve(false)
    })

    // 处理实时事件
    this.socket.on('session_updated', (data) => {
      this.emit('session_updated', data)
    })

    this.socket.on('workflow_state_changed', (data) => {
      this.emit('workflow_state_changed', data)
    })

    this.socket.on('performance_metrics', (data) => {
      this.emit('performance_metrics', data)
    })

    this.socket.on('system_status', (data) => {
      this.emit('system_status', data)
    })

    this.socket.on('error_occurred', (data) => {
      this.emit('error_occurred', data)
    })

    this.socket.on('notification', (data) => {
      this.emit('notification', data)
    })

    this.socket.on('user_activity', (data) => {
      this.emit('user_activity', data)
    })
  }

  // 处理连接错误
  private handleConnectionError(error: any) {
    this.emit('connection_error', { error, timestamp: Date.now() })
    this.handleReconnect()
  }

  // 处理重连
  private handleReconnect() {
    if (
      this.reconnectAttempts >= (this.config.maxReconnectAttempts || 5) ||
      this.isConnecting
    ) {
      return
    }

    this.reconnectAttempts++
    console.log(`尝试重连 (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`)

    setTimeout(() => {
      this.connect()
    }, this.config.reconnectInterval)
  }

  // 发送消息
  send(event: string, data: any): boolean {
    if (!this.socket?.connected) {
      console.warn('WebSocket未连接，无法发送消息')
      return false
    }

    try {
      this.socket.emit(event, data)
      return true
    } catch (error) {
      console.error('发送WebSocket消息失败:', error)
      return false
    }
  }

  // 订阅事件
  on(event: string, handler: Function) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, [])
    }
    this.eventHandlers.get(event)!.push(handler)
  }

  // 取消订阅事件
  off(event: string, handler?: Function) {
    const handlers = this.eventHandlers.get(event)
    if (!handlers) return

    if (handler) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    } else {
      this.eventHandlers.delete(event)
    }
  }

  // 触发事件
  private emit(event: string, data: any) {
    const handlers = this.eventHandlers.get(event)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data)
        } catch (error) {
          console.error(`处理事件 ${event} 时出错:`, error)
        }
      })
    }
  }

  // 获取连接状态
  isConnected(): boolean {
    return this.socket?.connected || false
  }

  // 获取连接信息
  getConnectionInfo() {
    return {
      connected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.config.maxReconnectAttempts,
      isConnecting: this.isConnecting,
      url: this.config.url,
    }
  }

  // 订阅会话更新
  subscribeToSession(sessionId: string) {
    this.send('subscribe_session', { sessionId })
  }

  // 取消订阅会话更新
  unsubscribeFromSession(sessionId: string) {
    this.send('unsubscribe_session', { sessionId })
  }

  // 订阅工作流更新
  subscribeToWorkflow(workflowId: string) {
    this.send('subscribe_workflow', { workflowId })
  }

  // 取消订阅工作流更新
  unsubscribeFromWorkflow(workflowId: string) {
    this.send('unsubscribe_workflow', { workflowId })
  }

  // 订阅系统指标
  subscribeToSystemMetrics() {
    this.send('subscribe_system_metrics')
  }

  // 取消订阅系统指标
  unsubscribeFromSystemMetrics() {
    this.send('unsubscribe_system_metrics')
  }

  // 发送心跳
  ping() {
    this.send('ping', { timestamp: Date.now() })
  }

  // 获取历史事件
  async getHistoryEvents(params?: {
    event?: string
    from?: number
    to?: number
    limit?: number
  }): Promise<WebSocketEvent[]> {
    return new Promise((resolve, reject) => {
      if (!this.isConnected()) {
        reject(new Error('WebSocket未连接'))
        return
      }

      const timeout = setTimeout(() => {
        reject(new Error('获取历史事件超时'))
      }, 5000)

      this.send('get_history_events', params)

      const handler = (data: WebSocketEvent[]) => {
        clearTimeout(timeout)
        this.off('history_events', handler)
        resolve(data)
      }

      this.on('history_events', handler)
    })
  }

  // 清理资源
  cleanup() {
    this.disconnect()
    this.eventHandlers.clear()
  }
}

export const websocketService = new WebSocketService({
  url: import.meta.env.VITE_WS_BASE_URL,
})

export default websocketService