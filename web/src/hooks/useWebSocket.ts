import { useEffect, useRef, useCallback } from 'react'
import { websocketService } from '@/services'
import { useAppStore } from '@/stores'

// WebSocket连接状态
export interface UseWebSocketOptions {
  autoConnect?: boolean
  reconnectOnMount?: boolean
  subscriptions?: string[]
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    autoConnect = true,
    reconnectOnMount = true,
    subscriptions = [],
  } = options

  const {
    setRealtimeConnected,
    setRealtimeLastUpdate,
    incrementReconnectAttempts,
    resetReconnectAttempts,
    addNotification,
  } = useAppStore()

  const isConnectedRef = useRef(false)
  const subscriptionsRef = useRef<Set<string>>(new Set())

  // 连接WebSocket
  const connect = useCallback(async () => {
    try {
      const connected = await websocketService.connect()
      if (connected) {
        isConnectedRef.current = true
        setRealtimeConnected(true)
        resetReconnectAttempts()
        
        // 重新订阅之前的订阅
        subscriptionsRef.current.forEach(sub => {
          if (sub.startsWith('session:')) {
            const sessionId = sub.replace('session:', '')
            websocketService.subscribeToSession(sessionId)
          } else if (sub.startsWith('workflow:')) {
            const workflowId = sub.replace('workflow:', '')
            websocketService.subscribeToWorkflow(workflowId)
          }
        })
      }
      return connected
    } catch (error) {
      console.error('WebSocket连接失败:', error)
      return false
    }
  }, [setRealtimeConnected, resetReconnectAttempts])

  // 断开WebSocket连接
  const disconnect = useCallback(() => {
    websocketService.disconnect()
    isConnectedRef.current = false
    setRealtimeConnected(false)
  }, [setRealtimeConnected])

  // 订阅会话
  const subscribeToSession = useCallback((sessionId: string) => {
    if (isConnectedRef.current) {
      websocketService.subscribeToSession(sessionId)
    }
    subscriptionsRef.current.add(`session:${sessionId}`)
  }, [])

  // 取消订阅会话
  const unsubscribeFromSession = useCallback((sessionId: string) => {
    if (isConnectedRef.current) {
      websocketService.unsubscribeFromSession(sessionId)
    }
    subscriptionsRef.current.delete(`session:${sessionId}`)
  }, [])

  // 订阅工作流
  const subscribeToWorkflow = useCallback((workflowId: string) => {
    if (isConnectedRef.current) {
      websocketService.subscribeToWorkflow(workflowId)
    }
    subscriptionsRef.current.add(`workflow:${workflowId}`)
  }, [])

  // 取消订阅工作流
  const unsubscribeFromWorkflow = useCallback((workflowId: string) => {
    if (isConnectedRef.current) {
      websocketService.unsubscribeFromWorkflow(workflowId)
    }
    subscriptionsRef.current.delete(`workflow:${workflowId}`)
  }, [])

  // 订阅系统指标
  const subscribeToSystemMetrics = useCallback(() => {
    if (isConnectedRef.current) {
      websocketService.subscribeToSystemMetrics()
    }
    subscriptionsRef.current.add('system_metrics')
  }, [])

  // 取消订阅系统指标
  const unsubscribeFromSystemMetrics = useCallback(() => {
    if (isConnectedRef.current) {
      websocketService.unsubscribeFromSystemMetrics()
    }
    subscriptionsRef.current.delete('system_metrics')
  }, [])

  // 发送消息
  const send = useCallback((event: string, data: any) => {
    return websocketService.send(event, data)
  }, [])

  // 获取连接信息
  const getConnectionInfo = useCallback(() => {
    return websocketService.getConnectionInfo()
  }, [])

  // 初始化连接
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  // 设置事件监听器
  useEffect(() => {
    // 连接状态变化
    websocketService.on('connected', () => {
      setRealtimeLastUpdate(Date.now())
    })

    websocketService.on('disconnected', () => {
      incrementReconnectAttempts()
    })

    websocketService.on('connection_error', () => {
      incrementReconnectAttempts()
    })

    // 会话更新
    websocketService.on('session_updated', (data) => {
      setRealtimeLastUpdate(Date.now())
      // 这里可以更新会话状态
    })

    // 工作流状态变化
    websocketService.on('workflow_state_changed', (data) => {
      setRealtimeLastUpdate(Date.now())
      // 这里可以更新工作流状态
    })

    // 性能指标
    websocketService.on('performance_metrics', (data) => {
      setRealtimeLastUpdate(Date.now())
      // 这里可以更新性能指标
    })

    // 系统状态
    websocketService.on('system_status', (data) => {
      setRealtimeLastUpdate(Date.now())
      // 这里可以更新系统状态
    })

    // 错误发生
    websocketService.on('error_occurred', (data) => {
      addNotification({
        type: 'error',
        title: '系统错误',
        message: data.message,
      })
    })

    // 通知
    websocketService.on('notification', (data) => {
      addNotification({
        type: data.type || 'info',
        title: data.title,
        message: data.message,
      })
    })

    // 用户活动
    websocketService.on('user_activity', (data) => {
      setRealtimeLastUpdate(Date.now())
      // 这里可以处理用户活动
    })

    // 清理函数
    return () => {
      websocketService.off('connected')
      websocketService.off('disconnected')
      websocketService.off('connection_error')
      websocketService.off('session_updated')
      websocketService.off('workflow_state_changed')
      websocketService.off('performance_metrics')
      websocketService.off('system_status')
      websocketService.off('error_occurred')
      websocketService.off('notification')
      websocketService.off('user_activity')
    }
  }, [setRealtimeLastUpdate, incrementReconnectAttempts, addNotification])

  // 处理初始订阅
  useEffect(() => {
    if (isConnectedRef.current) {
      subscriptions.forEach(sub => {
        if (sub.startsWith('session:')) {
          const sessionId = sub.replace('session:', '')
          websocketService.subscribeToSession(sessionId)
        } else if (sub.startsWith('workflow:')) {
          const workflowId = sub.replace('workflow:', '')
          websocketService.subscribeToWorkflow(workflowId)
        } else if (sub === 'system_metrics') {
          websocketService.subscribeToSystemMetrics()
        }
      })
    }
  }, [subscriptions])

  return {
    connect,
    disconnect,
    send,
    subscribeToSession,
    unsubscribeFromSession,
    subscribeToWorkflow,
    unsubscribeFromWorkflow,
    subscribeToSystemMetrics,
    unsubscribeFromSystemMetrics,
    getConnectionInfo,
    isConnected: websocketService.isConnected(),
  }
}

export default useWebSocket