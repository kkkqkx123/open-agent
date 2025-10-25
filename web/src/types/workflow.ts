import { Position } from 'reactflow'

// 工作流基础信息
export interface Workflow {
  id: string
  name: string
  description?: string
  status: 'draft' | 'active' | 'paused' | 'archived'
  version: string
  createdAt: string
  updatedAt: string
  createdBy: string
  tags?: string[]
  config?: WorkflowConfig
}

// 工作流配置
export interface WorkflowConfig {
  timeout?: number
  retryPolicy?: RetryPolicy
  errorHandling?: ErrorHandling
  notifications?: NotificationConfig
  variables?: Record<string, any>
}

// 重试策略
export interface RetryPolicy {
  maxAttempts: number
  backoffType: 'fixed' | 'exponential' | 'linear'
  initialDelay: number
  maxDelay: number
  multiplier?: number
}

// 错误处理
export interface ErrorHandling {
  strategy: 'stop' | 'continue' | 'retry' | 'fallback'
  fallbackNode?: string
  errorNotifications: boolean
}

// 通知配置
export interface NotificationConfig {
  onStart: boolean
  onComplete: boolean
  onError: boolean
  channels: ('email' | 'webhook' | 'in-app')[]
  recipients?: string[]
}

// 工作流节点
export interface WorkflowNode {
  id: string
  type: NodeType
  position: { x: number; y: number }
  data: NodeData
  style?: NodeStyle
  sourcePosition?: Position
  targetPosition?: Position
}

// 节点类型
export type NodeType = 'start' | 'process' | 'decision' | 'tool' | 'end' | 'error' | 'subworkflow'

// 节点数据
export interface NodeData {
  label: string
  description?: string
  parameters: Record<string, any>
  config: NodeConfig
  metadata: NodeMetadata
}

// 节点样式
export interface NodeStyle {
  backgroundColor?: string
  borderColor?: string
  borderWidth?: number
  borderRadius?: number
  width?: number
  height?: number
  fontSize?: number
  fontWeight?: string
  color?: string
}

// 节点配置
export interface NodeConfig {
  inputs: InputPort[]
  outputs: OutputPort[]
  properties: PropertyField[]
  validation: ValidationRule[]
  timeout?: number
}

// 输入端口
export interface InputPort {
  id: string
  name: string
  type: 'string' | 'number' | 'boolean' | 'object' | 'array' | 'file'
  required: boolean
  description?: string
  defaultValue?: any
}

// 输出端口
export interface OutputPort {
  id: string
  name: string
  type: 'string' | 'number' | 'boolean' | 'object' | 'array' | 'file'
  description?: string
}

// 属性字段
export interface PropertyField {
  id: string
  name: string
  type: 'text' | 'number' | 'boolean' | 'select' | 'multiselect' | 'textarea' | 'file' | 'json'
  label: string
  description?: string
  required: boolean
  defaultValue?: any
  options?: PropertyOption[]
  validation?: ValidationRule[]
}

// 属性选项
export interface PropertyOption {
  label: string
  value: any
  description?: string
}

// 验证规则
export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'minLength' | 'maxLength' | 'pattern' | 'custom'
  value?: any
  message: string
}

// 节点元数据
export interface NodeMetadata {
  category: string
  icon?: string
  tags?: string[]
  documentation?: string
  examples?: any[]
}

// 工作流连接
export interface WorkflowEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
  type?: EdgeType
  animated?: boolean
  style?: EdgeStyle
  data?: EdgeData
  condition?: string
}

// 边类型
export type EdgeType = 'default' | 'smoothstep' | 'straight' | 'bezier' | 'conditional' | 'loop'

// 边样式
export interface EdgeStyle {
  stroke?: string
  strokeWidth?: number
  strokeDasharray?: string
  label?: string
  labelStyle?: any
  labelBgStyle?: any
}

// 边数据
export interface EdgeData {
  label?: string
  condition?: string
  weight?: number
}

// 工作流执行
export interface WorkflowExecution {
  id: string
  workflowId: string
  status: 'running' | 'completed' | 'failed' | 'cancelled' | 'paused'
  startTime: string
  endTime?: string
  duration?: number
  currentNode?: string
  executionPath: ExecutionStep[]
  input?: any
  output?: any
  error?: ExecutionError
  metrics: ExecutionMetrics
}

// 执行步骤
export interface ExecutionStep {
  id: string
  nodeId: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  startTime: string
  endTime?: string
  duration?: number
  input?: any
  output?: any
  error?: string
  logs?: string[]
}

// 执行错误
export interface ExecutionError {
  nodeId: string
  type: 'system' | 'validation' | 'timeout' | 'business'
  message: string
  stack?: string
  timestamp: string
  retryable: boolean
}

// 执行指标
export interface ExecutionMetrics {
  totalNodes: number
  completedNodes: number
  failedNodes: number
  skippedNodes: number
  totalDuration: number
  averageNodeDuration: number
  memoryUsage?: number
  cpuUsage?: number
}

// 工作流模板
export interface WorkflowTemplate {
  id: string
  name: string
  description?: string
  category: string
  tags?: string[]
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  config?: WorkflowConfig
  preview?: string
  documentation?: string
  examples?: any[]
}

// 工作流统计
export interface WorkflowStats {
  totalWorkflows: number
  activeWorkflows: number
  draftWorkflows: number
  archivedWorkflows: number
  totalExecutions: number
  successfulExecutions: number
  failedExecutions: number
  averageExecutionTime: number
  topWorkflows: WorkflowUsageStats[]
}

// 工作流使用统计
export interface WorkflowUsageStats {
  workflowId: string
  workflowName: string
  executions: number
  successRate: number
  averageDuration: number
  lastExecution: string
}

// 工作流查询参数
export interface WorkflowQueryParams {
  status?: Workflow['status']
  category?: string
  tags?: string[]
  createdBy?: string
  dateFrom?: string
  dateTo?: string
  search?: string
  page?: number
  pageSize?: number
  sortBy?: 'createdAt' | 'updatedAt' | 'name' | 'status'
  sortOrder?: 'asc' | 'desc'
}

// 创建工作流参数
export interface WorkflowCreateParams {
  name: string
  description?: string
  category?: string
  tags?: string[]
  config?: WorkflowConfig
}

// 更新工作流参数
export interface WorkflowUpdateParams {
  name?: string
  description?: string
  status?: Workflow['status']
  tags?: string[]
  config?: WorkflowConfig
}

// 工作流验证结果
export interface WorkflowValidationResult {
  valid: boolean
  errors: ValidationError[]
  warnings: ValidationWarning[]
}

// 验证错误
export interface ValidationError {
  nodeId?: string
  edgeId?: string
  type: 'required' | 'connection' | 'configuration' | 'logic'
  message: string
  severity: 'error'
}

// 验证警告
export interface ValidationWarning {
  nodeId?: string
  edgeId?: string
  type: 'performance' | 'best_practice' | 'deprecated'
  message: string
  severity: 'warning'
}

// 导出所有类型
export type {
  Workflow,
  WorkflowConfig,
  RetryPolicy,
  ErrorHandling,
  NotificationConfig,
  WorkflowNode,
  NodeType,
  NodeData,
  NodeStyle,
  NodeConfig,
  InputPort,
  OutputPort,
  PropertyField,
  PropertyOption,
  ValidationRule,
  NodeMetadata,
  WorkflowEdge,
  EdgeType,
  EdgeStyle,
  EdgeData,
  WorkflowExecution,
  ExecutionStep,
  ExecutionError,
  ExecutionMetrics,
  WorkflowTemplate,
  WorkflowStats,
  WorkflowUsageStats,
  WorkflowQueryParams,
  WorkflowCreateParams,
  WorkflowUpdateParams,
  WorkflowValidationResult,
  ValidationError,
  ValidationWarning,
}