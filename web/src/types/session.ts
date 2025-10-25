import { Status } from './common'

// 会话基础信息
export interface Session {
  id: string
  name: string
  description?: string
  status: 'running' | 'completed' | 'failed' | 'paused'
  createdAt: string
  updatedAt: string
  duration?: number
  messageCount: number
  agentType: string
  config?: string
}

// 会话详细信息
export interface SessionDetail extends Session {
  messages: SessionMessage[]
  workflow?: WorkflowInfo
  performance: SessionPerformance
  errors: SessionError[]
  metadata: SessionMetadata
}

// 会话消息
export interface SessionMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  type: 'text' | 'image' | 'file' | 'tool_call' | 'tool_result'
  metadata?: {
    tokens?: number
    model?: string
    temperature?: number
    toolName?: string
    toolResult?: any
  }
}

// 工作流信息
export interface WorkflowInfo {
  id: string
  name: string
  status: 'running' | 'completed' | 'failed' | 'paused'
  currentNode?: string
  executionPath: string[]
  startTime: string
  endTime?: string
  nodes: WorkflowNode[]
}

// 工作流节点
export interface WorkflowNode {
  id: string
  type: 'start' | 'process' | 'decision' | 'tool' | 'end' | 'error'
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  startTime?: string
  endTime?: string
  duration?: number
  input?: any
  output?: any
  error?: string
  metadata?: Record<string, any>
}

// 会话性能
export interface SessionPerformance {
  totalTokens: number
  totalCost: number
  averageResponseTime: number
  totalResponseTime: number
  toolCalls: number
  errors: number
  metrics: PerformanceMetric[]
}

// 性能指标
export interface PerformanceMetric {
  timestamp: string
  responseTime: number
  tokens: number
  cost: number
  model: string
}

// 会话错误
export interface SessionError {
  id: string
  type: 'system' | 'network' | 'validation' | 'tool' | 'llm'
  message: string
  stack?: string
  timestamp: string
  nodeId?: string
  resolved: boolean
  severity: 'low' | 'medium' | 'high' | 'critical'
}

// 会话元数据
export interface SessionMetadata {
  userAgent?: string
  ip?: string
  location?: string
  referrer?: string
  tags?: string[]
  customFields?: Record<string, any>
}

// 创建会话参数
export interface SessionCreateParams {
  name: string
  description?: string
  agentType: string
  config?: string
  metadata?: SessionMetadata
}

// 更新会话参数
export interface SessionUpdateParams {
  name?: string
  description?: string
  status?: Session['status']
  config?: string
  metadata?: Partial<SessionMetadata>
}

// 会话查询参数
export interface SessionQueryParams {
  status?: Session['status']
  agentType?: string
  dateFrom?: string
  dateTo?: string
  search?: string
  tags?: string[]
  page?: number
  pageSize?: number
  sortBy?: 'createdAt' | 'updatedAt' | 'duration' | 'messageCount'
  sortOrder?: 'asc' | 'desc'
}

// 会话统计
export interface SessionStats {
  totalSessions: number
  runningSessions: number
  completedSessions: number
  failedSessions: number
  averageDuration: number
  totalMessages: number
  totalTokens: number
  totalCost: number
  topAgentTypes: AgentTypeStats[]
  recentActivity: ActivityStats[]
}

// 代理类型统计
export interface AgentTypeStats {
  agentType: string
  count: number
  percentage: number
}

// 活动统计
export interface ActivityStats {
  date: string
  sessions: number
  messages: number
  errors: number
}

// 会话导出选项
export interface SessionExportOptions {
  format: 'json' | 'csv' | 'pdf' | 'markdown'
  includeMessages: boolean
  includePerformance: boolean
  includeErrors: boolean
  includeMetadata: boolean
  dateRange?: {
    start: string
    end: string
  }
  filters?: SessionQueryParams
}

// 会话书签
export interface SessionBookmark {
  id: string
  sessionId: string
  name: string
  description?: string
  messageId?: string
  timestamp: string
  tags?: string[]
}

// 导出所有类型
export type {
  Session,
  SessionDetail,
  SessionMessage,
  WorkflowInfo,
  WorkflowNode,
  SessionPerformance,
  PerformanceMetric,
  SessionError,
  SessionMetadata,
  SessionCreateParams,
  SessionUpdateParams,
  SessionQueryParams,
  SessionStats,
  AgentTypeStats,
  ActivityStats,
  SessionExportOptions,
  SessionBookmark,
}