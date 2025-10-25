import { create } from 'zustand'
import { devtools, subscribeWithSelector } from 'zustand/middleware'
import { Session, Workflow, PerformanceMetrics, SystemStatus, Notification, Theme, ModuleType } from '@/types'
import { sessionService, workflowService, analyticsService } from '@/services'
import { storageService } from '@/services/storage'

// 应用状态接口
interface AppState {
  // 会话状态
  sessions: Session[]
  currentSession: Session | null
  sessionLoading: boolean
  sessionError: string | null
  
  // 工作流状态
  workflows: Workflow[]
  currentWorkflow: Workflow | null
  workflowLoading: boolean
  workflowError: string | null
  
  // 性能指标
  performanceMetrics: PerformanceMetrics | null
  systemStatus: SystemStatus | null
  metricsLoading: boolean
  
  // UI状态
  ui: {
    activeModule: ModuleType
    sidebarCollapsed: boolean
    theme: Theme
    language: string
    notifications: Notification[]
    loading: boolean
  }
  
  // 实时状态
  realtime: {
    connected: boolean
    lastUpdate: number
    reconnectAttempts: number
  }
  
  // 用户状态
  user: any | null
  authenticated: boolean
}

// 应用操作接口
interface AppActions {
  // 会话操作
  setSessions: (sessions: Session[]) => void
  setCurrentSession: (session: Session | null) => void
  loadSessions: () => Promise<void>
  createSession: (params: any) => Promise<Session>
  updateSession: (id: string, params: any) => Promise<void>
  deleteSession: (id: string) => Promise<void>
  
  // 工作流操作
  setWorkflows: (workflows: Workflow[]) => void
  setCurrentWorkflow: (workflow: Workflow | null) => void
  loadWorkflows: () => Promise<void>
  createWorkflow: (params: any) => Promise<Workflow>
  updateWorkflow: (id: string, params: any) => Promise<void>
  deleteWorkflow: (id: string) => Promise<void>
  
  // 性能指标操作
  setPerformanceMetrics: (metrics: PerformanceMetrics) => void
  setSystemStatus: (status: SystemStatus) => void
  loadMetrics: () => Promise<void>
  
  // UI操作
  setActiveModule: (module: ModuleType) => void
  toggleSidebar: () => void
  setTheme: (theme: Theme) => void
  setLanguage: (language: string) => void
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
  setLoading: (loading: boolean) => void
  
  // 实时操作
  setRealtimeConnected: (connected: boolean) => void
  setRealtimeLastUpdate: (timestamp: number) => void
  incrementReconnectAttempts: () => void
  resetReconnectAttempts: () => void
  
  // 用户操作
  setUser: (user: any) => void
  setAuthenticated: (authenticated: boolean) => void
  login: (credentials: any) => Promise<void>
  logout: () => void
  
  // 初始化操作
  initialize: () => Promise<void>
  reset: () => void
}

// 创建应用状态store
const useAppStore = create<AppState & AppActions>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // 初始状态
      sessions: [],
      currentSession: null,
      sessionLoading: false,
      sessionError: null,
      
      workflows: [],
      currentWorkflow: null,
      workflowLoading: false,
      workflowError: null,
      
      performanceMetrics: null,
      systemStatus: null,
      metricsLoading: false,
      
      ui: {
        activeModule: 'dashboard',
        sidebarCollapsed: storageService.getSidebarCollapsed(),
        theme: storageService.getTheme(),
        language: storageService.getLanguage(),
        notifications: storageService.getNotifications(),
        loading: false,
      },
      
      realtime: {
        connected: false,
        lastUpdate: 0,
        reconnectAttempts: 0,
      },
      
      user: storageService.getUser(),
      authenticated: !!storageService.getToken(),

      // 会话操作
      setSessions: (sessions) => set({ sessions }),
      
      setCurrentSession: (session) => {
        set({ currentSession: session })
        if (session) {
          storageService.addRecentSession(session)
        }
      },
      
      loadSessions: async () => {
        set({ sessionLoading: true, sessionError: null })
        try {
          const response = await sessionService.listSessions()
          set({ sessions: response.items, sessionLoading: false })
        } catch (error) {
          set({ 
            sessionError: error instanceof Error ? error.message : '加载会话失败',
            sessionLoading: false 
          })
        }
      },
      
      createSession: async (params) => {
        const session = await sessionService.createSession(params)
        set(state => ({ 
          sessions: [session, ...state.sessions],
          currentSession: session 
        }))
        storageService.addRecentSession(session)
        return session
      },
      
      updateSession: async (id, params) => {
        await sessionService.updateSession(id, params)
        set(state => ({
          sessions: state.sessions.map(s => s.id === id ? { ...s, ...params } : s),
          currentSession: state.currentSession?.id === id 
            ? { ...state.currentSession, ...params } 
            : state.currentSession
        }))
      },
      
      deleteSession: async (id) => {
        await sessionService.deleteSession(id)
        set(state => ({
          sessions: state.sessions.filter(s => s.id !== id),
          currentSession: state.currentSession?.id === id ? null : state.currentSession
        }))
        storageService.removeRecentSession(id)
      },

      // 工作流操作
      setWorkflows: (workflows) => set({ workflows }),
      
      setCurrentWorkflow: (workflow) => {
        set({ currentWorkflow: workflow })
        if (workflow) {
          storageService.addRecentWorkflow(workflow)
        }
      },
      
      loadWorkflows: async () => {
        set({ workflowLoading: true, workflowError: null })
        try {
          const response = await workflowService.listWorkflows()
          set({ workflows: response.items, workflowLoading: false })
        } catch (error) {
          set({ 
            workflowError: error instanceof Error ? error.message : '加载工作流失败',
            workflowLoading: false 
          })
        }
      },
      
      createWorkflow: async (params) => {
        const workflow = await workflowService.createWorkflow(params)
        set(state => ({ 
          workflows: [workflow, ...state.workflows],
          currentWorkflow: workflow 
        }))
        storageService.addRecentWorkflow(workflow)
        return workflow
      },
      
      updateWorkflow: async (id, params) => {
        await workflowService.updateWorkflow(id, params)
        set(state => ({
          workflows: state.workflows.map(w => w.id === id ? { ...w, ...params } : w),
          currentWorkflow: state.currentWorkflow?.id === id 
            ? { ...state.currentWorkflow, ...params } 
            : state.currentWorkflow
        }))
      },
      
      deleteWorkflow: async (id) => {
        await workflowService.deleteWorkflow(id)
        set(state => ({
          workflows: state.workflows.filter(w => w.id !== id),
          currentWorkflow: state.currentWorkflow?.id === id ? null : state.currentWorkflow
        }))
        storageService.removeRecentWorkflow(id)
      },

      // 性能指标操作
      setPerformanceMetrics: (metrics) => set({ performanceMetrics: metrics }),
      
      setSystemStatus: (status) => set({ systemStatus: status }),
      
      loadMetrics: async () => {
        set({ metricsLoading: true })
        try {
          const [metrics, status] = await Promise.all([
            analyticsService.getRealTimeMetrics(),
            analyticsService.getSystemStatus()
          ])
          set({ 
            performanceMetrics: metrics,
            systemStatus: status,
            metricsLoading: false 
          })
        } catch (error) {
          console.error('加载指标失败:', error)
          set({ metricsLoading: false })
        }
      },

      // UI操作
      setActiveModule: (module) => set(state => ({
        ui: { ...state.ui, activeModule: module }
      })),
      
      toggleSidebar: () => set(state => {
        const collapsed = !state.ui.sidebarCollapsed
        storageService.setSidebarCollapsed(collapsed)
        return {
          ui: { ...state.ui, sidebarCollapsed: collapsed }
        }
      }),
      
      setTheme: (theme) => set(state => {
        storageService.setTheme(theme)
        return {
          ui: { ...state.ui, theme }
        }
      }),
      
      setLanguage: (language) => set(state => {
        storageService.setLanguage(language)
        return {
          ui: { ...state.ui, language }
        }
      }),
      
      addNotification: (notification) => set(state => {
        const newNotification: Notification = {
          ...notification,
          id: `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          timestamp: Date.now()
        }
        const notifications = [newNotification, ...state.ui.notifications].slice(0, 50)
        storageService.setNotifications(notifications)
        return {
          ui: { ...state.ui, notifications }
        }
      }),
      
      removeNotification: (id) => set(state => {
        const notifications = state.ui.notifications.filter(n => n.id !== id)
        storageService.setNotifications(notifications)
        return {
          ui: { ...state.ui, notifications }
        }
      }),
      
      clearNotifications: () => set(state => {
        storageService.clearNotifications()
        return {
          ui: { ...state.ui, notifications: [] }
        }
      }),
      
      setLoading: (loading) => set(state => ({
        ui: { ...state.ui, loading }
      })),

      // 实时操作
      setRealtimeConnected: (connected) => set(state => ({
        realtime: { ...state.realtime, connected }
      })),
      
      setRealtimeLastUpdate: (timestamp) => set(state => ({
        realtime: { ...state.realtime, lastUpdate: timestamp }
      })),
      
      incrementReconnectAttempts: () => set(state => ({
        realtime: { 
          ...state.realtime, 
          reconnectAttempts: state.realtime.reconnectAttempts + 1 
        }
      })),
      
      resetReconnectAttempts: () => set(state => ({
        realtime: { ...state.realtime, reconnectAttempts: 0 }
      })),

      // 用户操作
      setUser: (user) => {
        storageService.setUser(user)
        set({ user })
      },
      
      setAuthenticated: (authenticated) => set({ authenticated }),
      
      login: async (credentials) => {
        // 这里应该调用登录API
        // const response = await authService.login(credentials)
        // storageService.setToken(response.token)
        // setUser(response.user)
        // setAuthenticated(true)
      },
      
      logout: () => {
        storageService.removeToken()
        storageService.removeUser()
        set({ user: null, authenticated: false })
      },

      // 初始化操作
      initialize: async () => {
        set(state => ({ ui: { ...state.ui, loading: true } }))
        
        try {
          // 加载初始数据
          await Promise.all([
            get().loadSessions(),
            get().loadWorkflows(),
            get().loadMetrics()
          ])
        } catch (error) {
          console.error('初始化失败:', error)
        } finally {
          set(state => ({ ui: { ...state.ui, loading: false } }))
        }
      },
      
      reset: () => {
        set({
          sessions: [],
          currentSession: null,
          sessionLoading: false,
          sessionError: null,
          workflows: [],
          currentWorkflow: null,
          workflowLoading: false,
          workflowError: null,
          performanceMetrics: null,
          systemStatus: null,
          metricsLoading: false,
          ui: {
            activeModule: 'dashboard',
            sidebarCollapsed: false,
            theme: 'light',
            language: 'zh-CN',
            notifications: [],
            loading: false,
          },
          realtime: {
            connected: false,
            lastUpdate: 0,
            reconnectAttempts: 0,
          },
          user: null,
          authenticated: false,
        })
      },
    })),
    {
      name: 'app-store',
    }
  )
)

export default useAppStore