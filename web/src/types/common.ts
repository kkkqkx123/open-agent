// 通用响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  success: boolean
}

// 分页参数
export interface PaginationParams {
  page: number
  pageSize: number
  total?: number
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
}

// 排序参数
export interface SortParams {
  field: string
  order: 'asc' | 'desc'
}

// 过滤参数
export interface FilterParams {
  [key: string]: any
}

// 查询参数
export interface QueryParams extends PaginationParams {
  sort?: SortParams
  filter?: FilterParams
  search?: string
}

// 错误类型
export interface ErrorInfo {
  type: 'javascript' | 'promise' | 'react' | 'network'
  message: string
  filename?: string
  lineno?: number
  colno?: number
  stack?: string
  componentStack?: string
  timestamp: number
}

// 通知类型
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  timestamp: number
}

// 主题类型
export type Theme = 'light' | 'dark'

// 语言类型
export type Locale = 'zh-CN' | 'en-US'

// 模块类型
export type ModuleType = 'dashboard' | 'workflows' | 'analytics' | 'errors' | 'history' | 'config'

// 状态类型
export type Status = 'idle' | 'loading' | 'success' | 'error'

// 时间范围
export interface DateRange {
  start: Date
  end: Date
}

// 菜单项
export interface MenuItem {
  key: string
  label: string
  icon?: React.ReactNode
  path?: string
  children?: MenuItem[]
  disabled?: boolean
}

// 快速访问链接
export interface QuickAccessLink {
  name: string
  url: string
  icon: string
  description?: string
}

// 实时连接状态
export interface RealtimeStatus {
  connected: boolean
  lastUpdate: number
  reconnectAttempts: number
}

// 性能指标
export interface PerformanceMetrics {
  responseTime: number
  throughput: number
  errorRate: number
  memoryUsage?: number
  cpuUsage?: number
  timestamp: number
}

// 系统状态
export interface SystemStatus {
  status: 'healthy' | 'warning' | 'error'
  uptime: number
  version: string
  environment: string
  lastCheck: number
}

// 导出所有类型
export type {
  ApiResponse,
  PaginationParams,
  PaginatedResponse,
  SortParams,
  FilterParams,
  QueryParams,
  ErrorInfo,
  Notification,
  Theme,
  Locale,
  ModuleType,
  Status,
  DateRange,
  MenuItem,
  QuickAccessLink,
  RealtimeStatus,
  PerformanceMetrics,
  SystemStatus,
}