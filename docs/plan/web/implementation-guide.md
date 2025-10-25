# Web前端实施指南

## 1. 项目启动清单

### 1.1 环境准备 ✅
- [ ] Node.js 18+ 安装
- [ ] npm 9+ 安装
- [ ] Git 配置
- [ ] VSCode 插件安装（ESLint, Prettier, TypeScript）

### 1.2 项目初始化 ✅
```bash
# 创建项目目录
mkdir web && cd web

# 初始化项目
npm create vite@latest . --template react-ts

# 安装核心依赖
npm install react react-dom react-router-dom
npm install antd @ant-design/icons
npm install zustand @tanstack/react-query
npm install axios socket.io-client
npm install react-flow-renderer
npm install echarts echarts-for-react

# 安装开发依赖
npm install -D @types/react @types/react-dom
npm install -D typescript @vitejs/plugin-react
npm install -D eslint prettier tailwindcss
npm install -D vitest @vitest/ui
```

### 1.3 配置文件设置 ✅
- [ ] 复制 `project-setup.md` 中的配置文件
- [ ] 配置 TypeScript 路径别名
- [ ] 设置 ESLint 和 Prettier
- [ ] 配置 Tailwind CSS

## 2. 开发阶段实施

### 2.1 第一阶段：基础架构 (Week 1-2)

#### 2.1.1 目录结构搭建
```bash
src/
├── components/          # 共享组件
│   ├── layout/         # 布局组件
│   ├── common/         # 通用组件
│   └── charts/         # 图表组件
├── modules/            # 功能模块
│   ├── dashboard/      # 仪表板
│   ├── workflows/      # 工作流管理
│   ├── analytics/      # 性能分析
│   ├── errors/         # 错误管理
│   ├── history/        # 历史数据
│   └── config/         # 配置管理
├── services/           # 服务层
│   ├── api/           # REST API
│   ├── websocket/     # WebSocket服务
│   └── storage/       # 本地存储
├── stores/            # 状态管理
├── hooks/             # 自定义Hooks
├── utils/             # 工具函数
└── types/             # 类型定义
```

#### 2.1.2 核心服务实现
```typescript
// src/services/api/base.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import { message } from 'antd'

class BaseService {
  protected api: AxiosInstance

  constructor(baseURL: string) {
    this.api = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // 请求拦截器
    this.api.interceptors.request.use(
      config => {
        // 添加认证token
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      error => Promise.reject(error)
    )

    // 响应拦截器
    this.api.interceptors.response.use(
      response => response.data,
      error => {
        if (error.response?.status === 401) {
          // 处理未认证
          window.location.href = '/login'
        } else if (error.response?.status === 500) {
          message.error('服务器错误，请稍后重试')
        }
        return Promise.reject(error)
      }
    )
  }
}

// src/services/api/session.ts
import { BaseService } from './base'
import { Session, SessionDetail, SessionCreateParams } from '@/types/session'

class SessionService extends BaseService {
  constructor() {
    super(import.meta.env.VITE_API_BASE_URL + '/sessions')
  }

  async listSessions(): Promise<Session[]> {
    return this.api.get('/')
  }

  async getSession(id: string): Promise<SessionDetail> {
    return this.api.get(`/${id}`)
  }

  async createSession(params: SessionCreateParams): Promise<Session> {
    return this.api.post('/', params)
  }

  async deleteSession(id: string): Promise<void> {
    return this.api.delete(`/${id}`)
  }
}

export const sessionService = new SessionService()
```

#### 2.1.3 WebSocket服务实现
```typescript
// src/services/websocket/index.ts
import { io, Socket } from 'socket.io-client'
import { message } from 'antd'

interface WebSocketServiceConfig {
  url: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

class WebSocketService {
  private socket: Socket | null = null
  private config: WebSocketServiceConfig
  private reconnectAttempts = 0
  private eventHandlers = new Map<string, Function[]>()

  constructor(config: WebSocketServiceConfig) {
    this.config = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 5,
      ...config
    }
  }

  connect() {
    if (this.socket?.connected) return

    this.socket = io(this.config.url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: this.config.reconnectInterval,
      reconnectionAttempts: this.config.maxReconnectAttempts
    })

    this.setupEventListeners()
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  private setupEventListeners() {
    if (!this.socket) return

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
      message.success('实时连接已建立')
    })

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
      message.warning('实时连接已断开')
    })

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
      message.error('实时连接出错')
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
  }

  on(event: string, handler: Function) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, [])
    }
    this.eventHandlers.get(event)!.push(handler)
  }

  off(event: string, handler: Function) {
    const handlers = this.eventHandlers.get(event)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  private emit(event: string, data: any) {
    const handlers = this.eventHandlers.get(event)
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }
  }
}

export const websocketService = new WebSocketService({
  url: import.meta.env.VITE_WS_BASE_URL
})
```

#### 2.1.4 状态管理实现
```typescript
// src/stores/app.ts
import { create } from 'zustand'
import { devtools, subscribeWithSelector } from 'zustand/middleware'
import { Session, Workflow, PerformanceMetrics } from '@/types'

interface AppState {
  // 会话状态
  sessions: Session[]
  currentSession: Session | null
  sessionLoading: boolean
  
  // 工作流状态
  workflows: Workflow[]
  currentWorkflow: Workflow | null
  workflowState: any
  
  // 性能指标
  performanceMetrics: PerformanceMetrics
  systemMetrics: any
  
  // UI状态
  ui: {
    activeModule: string
    sidebarCollapsed: boolean
    theme: 'light' | 'dark'
    notifications: Notification[]
  }
  
  // 实时状态
  realtime: {
    connected: boolean
    lastUpdate: number
  }
}

interface AppActions {
  // 会话操作
  setSessions: (sessions: Session[]) => void
  setCurrentSession: (session: Session | null) => void
  loadSessions: () => Promise<void>
  
  // 工作流操作
  setWorkflows: (workflows: Workflow[]) => void
  setCurrentWorkflow: (workflow: Workflow | null) => void
  updateWorkflowState: (state: any) => void
  
  // UI操作
  setActiveModule: (module: string) => void
  toggleSidebar: () => void
  toggleTheme: () => void
  addNotification: (notification: Notification) => void
  removeNotification: (id: string) => void
  
  // 实时操作
  setRealtimeConnected: (connected: boolean) => void
}

const useAppStore = create<AppState & AppActions>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // 初始状态
      sessions: [],
      currentSession: null,
      sessionLoading: false,
      workflows: [],
      currentWorkflow: null,
      workflowState: null,
      performanceMetrics: {},
      systemMetrics: {},
      ui: {
        activeModule: 'dashboard',
        sidebarCollapsed: false,
        theme: 'light',
        notifications: []
      },
      realtime: {
        connected: false,
        lastUpdate: 0
      },

      // 会话操作
      setSessions: (sessions) => set({ sessions }),
      setCurrentSession: (session) => set({ currentSession: session }),
      loadSessions: async () => {
        set({ sessionLoading: true })
        try {
          const sessions = await sessionService.listSessions()
          set({ sessions, sessionLoading: false })
        } catch (error) {
          set({ sessionLoading: false })
          throw error
        }
      },

      // 工作流操作
      setWorkflows: (workflows) => set({ workflows }),
      setCurrentWorkflow: (workflow) => set({ currentWorkflow: workflow }),
      updateWorkflowState: (state) => set({ workflowState: state }),

      // UI操作
      setActiveModule: (module) => set(state => ({
        ui: { ...state.ui, activeModule: module }
      })),
      toggleSidebar: () => set(state => ({
        ui: { ...state.ui, sidebarCollapsed: !state.ui.sidebarCollapsed }
      })),
      toggleTheme: () => set(state => ({
        ui: { ...state.ui, theme: state.ui.theme === 'light' ? 'dark' : 'light' }
      })),
      addNotification: (notification) => set(state => ({
        ui: { 
          ...state.ui, 
          notifications: [...state.ui.notifications, notification] 
        }
      })),
      removeNotification: (id) => set(state => ({
        ui: {
          ...state.ui,
          notifications: state.ui.notifications.filter(n => n.id !== id)
        }
      })),

      // 实时操作
      setRealtimeConnected: (connected) => set(state => ({
        realtime: { ...state.realtime, connected }
      }))
    })),
    {
      name: 'app-store'
    }
  )
)

export default useAppStore
```

### 2.2 第二阶段：核心界面开发 (Week 3-4)

#### 2.2.1 布局组件实现
```typescript
// src/components/layout/AppLayout.tsx
import React from 'react'
import { Layout } from 'antd'
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons'
import AppHeader from './AppHeader'
import AppSidebar from './AppSidebar'
import AppContent from './AppContent'
import useAppStore from '@/stores/app'

const { Sider, Content } = Layout

const AppLayout: React.FC = () => {
  const { ui, toggleSidebar } = useAppStore()

  return (
    <Layout className="app-layout" style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={ui.sidebarCollapsed}
        width={280}
        className="app-sidebar"
        theme={ui.theme}
      >
        <AppSidebar />
      </Sider>
      
      <Layout>
        <AppHeader 
          collapsed={ui.sidebarCollapsed}
          onToggle={toggleSidebar}
        />
        <Content className="app-content">
          <AppContent />
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout
```

#### 2.2.2 仪表板模块实现
```typescript
// src/modules/dashboard/Dashboard.tsx
import React from 'react'
import { Row, Col, Card, Statistic, Progress } from 'antd'
import { 
  DashboardOutlined, 
  NodeIndexOutlined, 
  ClockCircleOutlined,
  DollarOutlined 
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { sessionService } from '@/services/api/session'
import { workflowService } from '@/services/api/workflow'
import MetricsChart from '@/components/charts/MetricsChart'
import useAppStore from '@/stores/app'

const Dashboard: React.FC = () => {
  const { setActiveModule } = useAppStore()
  
  // 获取会话数据
  const { data: sessions = [] } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => sessionService.listSessions()
  })

  // 获取工作流数据
  const { data: workflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowService.listWorkflows()
  })

  // 计算统计数据
  const stats = {
    totalSessions: sessions.length,
    activeSessions: sessions.filter(s => s.status === 'running').length,
    totalWorkflows: workflows.length,
    avgResponseTime: 245, // 模拟数据
    successRate: 98.5, // 模拟数据
    costEstimate: 12.34 // 模拟数据
  }

  React.useEffect(() => {
    setActiveModule('dashboard')
  }, [setActiveModule])

  return (
    <div className="dashboard-module">
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总会话数"
              value={stats.totalSessions}
              prefix={<DashboardOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃会话"
              value={stats.activeSessions}
              prefix={<NodeIndexOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={stats.avgResponseTime}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="成功率"
              value={stats.successRate}
              precision={1}
              suffix="%"
              prefix={<Progress percent={stats.successRate} size="small" />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="性能趋势">
            <MetricsChart 
              data={[]} // 实际数据
              height={300}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="成本分析">
            <MetricsChart 
              data={[]} // 实际数据
              height={300}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="最近会话">
            {/* 会话列表组件 */}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="系统状态">
            {/* 系统状态组件 */}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
```

### 2.3 第三阶段：高级功能 (Week 5-7)

#### 2.3.1 工作流可视化实现
参考 `workflow-visualization.md` 中的详细实现方案

#### 2.3.2 性能分析实现
```typescript
// src/modules/analytics/PerformanceAnalytics.tsx
import React, { useState, useEffect } from 'react'
import { Card, Tabs, DatePicker, Button, Space } from 'antd'
import { Line, Bar, Pie } from '@ant-design/charts'
import { useQuery } from '@tanstack/react-query'
import { analyticsService } from '@/services/api/analytics'
import useAppStore from '@/stores/app'

const { RangePicker } = DatePicker
const { TabPane } = Tabs

const PerformanceAnalytics: React.FC = () => {
  const { setActiveModule } = useAppStore()
  const [dateRange, setDateRange] = useState<[moment.Moment, moment.Moment]>([
    moment().subtract(7, 'days'),
    moment()
  ])

  // 获取性能数据
  const { data: performanceData } = useQuery({
    queryKey: ['performance', dateRange],
    queryFn: () => analyticsService.getPerformanceData({
      startDate: dateRange[0].toISOString(),
      endDate: dateRange[1].toISOString()
    })
  })

  // 响应时间趋势图配置
  const responseTimeConfig = {
    data: performanceData?.responseTimeTrend || [],
    xField: 'timestamp',
    yField: 'responseTime',
    seriesField: 'type',
    smooth: true,
    animation: {
      appear: {
        animation: 'fade-in',
        duration: 1000
      }
    },
    tooltip: {
      showMarkers: true,
      marker: {
        style: {
          fill: '#1890ff',
          stroke: '#1890ff',
          lineWidth: 2
        }
      }
    }
  }

  // 错误分布饼图配置
  const errorDistributionConfig = {
    data: performanceData?.errorDistribution || [],
    angleField: 'count',
    colorField: 'errorType',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} {percentage}'
    },
    interactions: [{ type: 'element-active' }]
  }

  React.useEffect(() => {
    setActiveModule('analytics')
  }, [setActiveModule])

  return (
    <div className="performance-analytics">
      <Card>
        <div className="analytics-header">
          <h2>性能分析</h2>
          <Space>
            <RangePicker 
              value={dateRange}
              onChange={setDateRange}
              ranges={{
                '今天': [moment(), moment()],
                '本周': [moment().startOf('week'), moment().endOf('week')],
                '本月': [moment().startOf('month'), moment().endOf('month')]
              }}
            />
            <Button type="primary" icon={<DownloadOutlined />}>
              导出报告
            </Button>
          </Space>
        </div>

        <Tabs defaultActiveKey="overview">
          <TabPane tab="概览" key="overview">
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Card title="响应时间趋势">
                  <Line {...responseTimeConfig} />
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card title="错误分布">
                  <Pie {...errorDistributionConfig} />
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card title="请求量统计">
                  <Bar {...requestVolumeConfig} />
                </Card>
              </Col>
            </Row>
          </TabPane>
          
          <TabPane tab="详细分析" key="detailed">
            {/* 详细分析内容 */}
          </TabPane>
          
          <TabPane tab="成本分析" key="cost">
            {/* 成本分析内容 */}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default PerformanceAnalytics
```

### 2.4 第四阶段：集成与优化 (Week 8-10)

#### 2.4.1 TUI集成实现
```typescript
// src/services/integration/tui-integration.ts
class TUIIntegrationService {
  private baseUrl: string = 'http://localhost:8080/maaf/web'

  // 获取TUI状态
  async getTUIStatus(): Promise<TUIStatus> {
    const response = await fetch(`${this.baseUrl}/api/tui/status`)
    return response.json()
  }

  // 同步会话
  async syncSession(sessionId: string): Promise<void> {
    await fetch(`${this.baseUrl}/api/tui/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionId })
    })
  }

  // 打开Web界面
  openWebInterface(module: string = 'dashboard'): void {
    const url = `${this.baseUrl}/${module}`
    window.open(url, '_blank')
  }

  // 获取快速访问链接
  getQuickAccessLinks(): QuickAccessLink[] {
    return [
      { name: '仪表板', url: `${this.baseUrl}/dashboard`, icon: 'dashboard' },
      { name: '工作流', url: `${this.baseUrl}/workflows`, icon: 'workflow' },
      { name: '性能分析', url: `${this.baseUrl}/analytics`, icon: 'analytics' },
      { name: '错误管理', url: `${this.baseUrl}/errors`, icon: 'error' },
      { name: '历史数据', url: `${this.baseUrl}/history`, icon: 'history' },
      { name: '配置管理', url: `${this.baseUrl}/config`, icon: 'setting' }
    ]
  }
}

export const tuiIntegration = new TUIIntegrationService()
```

#### 2.4.2 性能优化实现
```typescript
// src/utils/performance-optimization.ts
// 虚拟滚动实现
export const useVirtualScroll = (items: any[], itemHeight: number, containerHeight: number) => {
  const [startIndex, setStartIndex] = useState(0)
  const [endIndex, setEndIndex] = useState(0)

  const visibleItems = useMemo(() => {
    return items.slice(startIndex, endIndex + 1)
  }, [items, startIndex, endIndex])

  const handleScroll = (scrollTop: number) => {
    const newStartIndex = Math.floor(scrollTop / itemHeight)
    const visibleCount = Math.ceil(containerHeight / itemHeight)
    const newEndIndex = Math.min(newStartIndex + visibleCount, items.length - 1)

    setStartIndex(newStartIndex)
    setEndIndex(newEndIndex)
  }

  return { visibleItems, handleScroll }
}

// 防抖节流实现
export const useDebounce = (callback: Function, delay: number) => {
  const timeoutRef = useRef<NodeJS.Timeout>()

  return useCallback((...args: any[]) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    timeoutRef.current = setTimeout(() => {
      callback(...args)
    }, delay)
  }, [callback, delay])
}

// 组件懒加载
export const LazyComponent = React.lazy(() => 
  import('@/components/HeavyComponent')
)

// 图片懒加载
export const LazyImage: React.FC<{ src: string; alt: string }> = ({ src, alt }) => {
  const [imageSrc, setImageSrc] = useState('')
  const [imageRef, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1
  })

  useEffect(() => {
    if (inView) {
      setImageSrc(src)
    }
  }, [inView, src])

  return <img ref={imageRef} src={imageSrc} alt={alt} loading="lazy" />
}
```

## 3. 测试策略

### 3.1 单元测试
```typescript
// src/modules/dashboard/__tests__/Dashboard.test.tsx
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from '../Dashboard'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false }
  }
})

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
)

describe('Dashboard', () => {
  it('renders dashboard with stats', () => {
    render(<Dashboard />, { wrapper })
    
    expect(screen.getByText('总会话数')).toBeInTheDocument()
    expect(screen.getByText('活跃会话')).toBeInTheDocument()
    expect(screen.getByText('平均响应时间')).toBeInTheDocument()
    expect(screen.getByText('成功率')).toBeInTheDocument()
  })

  it('displays performance charts', () => {
    render(<Dashboard />, { wrapper })
    
    expect(screen.getByText('性能趋势')).toBeInTheDocument()
    expect(screen.getByText('成本分析')).toBeInTheDocument()
  })
})
```

### 3.2 集成测试
```typescript
// src/services/api/__tests__/session.test.ts
import { describe, it, expect, vi } from 'vitest'
import { sessionService } from '../session'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn()
    }))
  }
}))

describe('SessionService', () => {
  it('lists sessions successfully', async () => {
    const mockSessions = [
      { id: '1', name: 'Session 1', status: 'running' },
      { id: '2', name: 'Session 2', status: 'completed' }
    ]

    // Mock implementation
    sessionService.api.get = vi.fn().mockResolvedValue({ data: mockSessions })

    const sessions = await sessionService.listSessions()
    expect(sessions).toEqual(mockSessions)
    expect(sessionService.api.get).toHaveBeenCalledWith('/')
  })

  it('creates session with params', async () => {
    const params = { name: 'New Session', config: 'test.yaml' }
    const mockResponse = { id: '3', ...params }

    sessionService.api.post = vi.fn().mockResolvedValue({ data: mockResponse })

    const session = await sessionService.createSession(params)
    expect(session).toEqual(mockResponse)
    expect(sessionService.api.post).toHaveBeenCalledWith('/', params)
  })
})
```

## 4. 部署配置

### 4.1 构建配置
```typescript
// vite.config.ts - 生产环境优化
export default defineConfig({
  build: {
    target: 'es2015',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log']
      }
    },
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (id.includes('node_modules')) {
            if (id.includes('react')) return 'react-vendor'
            if (id.includes('antd')) return 'antd-vendor'
            if (id.includes('echarts')) return 'charts-vendor'
            if (id.includes('react-flow')) return 'flow-vendor'
            return 'vendor'
          }
        }
      }
    },
    chunkSizeWarningLimit: 1000,
    reportCompressedSize: false
  }
})
```

### 4.2 Docker配置
```dockerfile
# Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./
RUN npm ci --only=production

# 复制源码
COPY . .

# 构建应用
RUN npm run build

# 生产镜像
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 4.3 Nginx配置
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # 前端路由支持
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API代理
        location /api {
            proxy_pass http://backend:8080/maaf/web/api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket代理
        location /ws {
            proxy_pass http://backend:8080/maaf/web/ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## 5. 监控和维护

### 5.1 性能监控
```typescript
// src/utils/performance-monitor.ts
class PerformanceMonitor {
  private metrics: PerformanceMetrics = {}

  startMonitoring() {
    // 监控页面加载时间
    window.addEventListener('load', () => {
      const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart
      this.recordMetric('page_load_time', loadTime)
    })

    // 监控API响应时间
    this.monitorAPIPerformance()

    // 监控内存使用
    if (performance.memory) {
      setInterval(() => {
        this.recordMetric('memory_usage', performance.memory.usedJSHeapSize)
      }, 5000)
    }
  }

  private monitorAPIPerformance() {
    const originalFetch = window.fetch
    window.fetch = async (...args) => {
      const start = performance.now()
      try {
        const response = await originalFetch(...args)
        const duration = performance.now() - start
        this.recordMetric('api_response_time', duration)
        return response
      } catch (error) {
        const duration = performance.now() - start
        this.recordMetric('api_error_time', duration)
        throw error
      }
    }
  }

  private recordMetric(name: string, value: number) {
    this.metrics[name] = value
    
    // 发送到监控服务
    if (window.gtag) {
      window.gtag('event', 'performance_metric', {
        metric_name: name,
        metric_value: value
      })
    }
  }

  getMetrics() {
    return { ...this.metrics }
  }
}

export const performanceMonitor = new PerformanceMonitor()
```

### 5.2 错误监控
```typescript
// src/utils/error-monitor.ts
class ErrorMonitor {
  init() {
    // 监听JavaScript错误
    window.addEventListener('error', (event) => {
      this.reportError({
        type: 'javascript',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack
      })
    })

    // 监听未处理的Promise拒绝
    window.addEventListener('unhandledrejection', (event) => {
      this.reportError({
        type: 'promise',
        message: event.reason?.message || 'Unhandled Promise Rejection',
        stack: event.reason?.stack
      })
    })

    // 监听React错误
    if (process.env.NODE_ENV === 'production') {
      this.setupReactErrorBoundary()
    }
  }

  private setupReactErrorBoundary() {
    // 使用错误边界组件包装应用
    class ErrorBoundary extends React.Component {
      componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        errorMonitor.reportError({
          type: 'react',
          message: error.message,
          stack: error.stack,
          componentStack: errorInfo.componentStack
        })
      }

      render() {
        return this.props.children
      }
    }
  }

  reportError(error: ErrorInfo) {
    // 发送到错误监控服务
    console.error('Error reported:', error)
    
    // 这里可以集成Sentry、LogRocket等服务
    if (window.Sentry) {
      window.Sentry.captureException(error)
    }
  }
}

export const errorMonitor = new ErrorMonitor()
```

这个实施指南提供了从项目启动到部署的完整流程，确保Web前端项目能够顺利实施并与现有TUI系统无缝集成。