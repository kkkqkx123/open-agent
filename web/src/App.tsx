import React, { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, App as AntdApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { useAppStore } from '@/stores'
import { useWebSocket } from '@/hooks'
import AppLayout from '@/components/layout/AppLayout'
import Dashboard from '@/modules/dashboard/Dashboard'
import WorkflowList from '@/modules/workflows/WorkflowList'
import WorkflowEditor from '@/modules/workflows/WorkflowEditor'
import Analytics from '@/modules/analytics/Analytics'
import ErrorManagement from '@/modules/errors/ErrorManagement'
import History from '@/modules/history/History'
import Config from '@/modules/config/Config'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import ErrorBoundary from '@/components/common/ErrorBoundary'
import './App.css'

const App: React.FC = () => {
  const {
    ui,
    initialize,
    setTheme,
    addNotification,
    setRealtimeConnected,
  } = useAppStore()

  // WebSocket连接
  useWebSocket({
    autoConnect: true,
    subscriptions: ['system_metrics'],
  })

  // 初始化应用
  useEffect(() => {
    initialize()
  }, [initialize])

  // 应用主题
  useEffect(() => {
    const root = document.documentElement
    if (ui.theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [ui.theme])

  // 监听系统主题变化
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    
    const handleChange = (e: MediaQueryListEvent) => {
      if (e.matches) {
        setTheme('dark')
      } else {
        setTheme('light')
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [setTheme])

  // 监听网络状态
  useEffect(() => {
    const handleOnline = () => {
      setRealtimeConnected(true)
      addNotification({
        type: 'success',
        title: '网络连接恢复',
        message: '已重新连接到网络',
      })
    }

    const handleOffline = () => {
      setRealtimeConnected(false)
      addNotification({
        type: 'warning',
        title: '网络连接断开',
        message: '请检查网络连接',
      })
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [setRealtimeConnected, addNotification])

  // 监听页面可见性变化
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // 页面重新可见时，刷新数据
        initialize()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [initialize])

  // 监听窗口大小变化
  useEffect(() => {
    const handleResize = () => {
      // 可以在这里处理响应式布局逻辑
      const width = window.innerWidth
      if (width < 768) {
        // 移动端布局
        document.body.classList.add('mobile')
      } else {
        // 桌面端布局
        document.body.classList.remove('mobile')
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl/Cmd + K: 快速搜索
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault()
        // 这里可以打开搜索对话框
      }

      // Ctrl/Cmd + /: 显示快捷键帮助
      if ((event.ctrlKey || event.metaKey) && event.key === '/') {
        event.preventDefault()
        // 这里可以显示快捷键帮助
      }

      // Esc: 关闭模态框或清除选择
      if (event.key === 'Escape') {
        // 这里可以处理ESC键逻辑
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  // 错误处理
  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      console.error('全局错误:', event.error)
      addNotification({
        type: 'error',
        title: '系统错误',
        message: event.error?.message || '发生了未知错误',
      })
    }

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      console.error('未处理的Promise拒绝:', event.reason)
      addNotification({
        type: 'error',
        title: '系统错误',
        message: event.reason?.message || '发生了未知错误',
      })
    }

    window.addEventListener('error', handleError)
    window.addEventListener('unhandledrejection', handleUnhandledRejection)

    return () => {
      window.removeEventListener('error', handleError)
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
    }
  }, [addNotification])

  // 如果正在加载，显示加载动画
  if (ui.loading) {
    return <LoadingSpinner />
  }

  return (
    <ErrorBoundary>
      <ConfigProvider
        locale={zhCN}
        theme={{
          algorithm: ui.theme === 'dark' ? 'darkAlgorithm' : 'defaultAlgorithm',
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
            fontSize: 14,
          },
        }}
      >
        <AntdApp>
          <div className={`app ${ui.theme}`}>
            <Routes>
              <Route path="/" element={<AppLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="workflows" element={<WorkflowList />} />
                <Route path="workflows/:id" element={<WorkflowEditor />} />
                <Route path="workflows/:id/edit" element={<WorkflowEditor />} />
                <Route path="analytics" element={<Analytics />} />
                <Route path="errors" element={<ErrorManagement />} />
                <Route path="history" element={<History />} />
                <Route path="config" element={<Config />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Route>
            </Routes>
          </div>
        </AntdApp>
      </ConfigProvider>
    </ErrorBoundary>
  )
}

export default App