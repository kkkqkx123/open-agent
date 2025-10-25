import { BaseService } from './base'
import {
  Workflow,
  WorkflowNode,
  WorkflowEdge,
  WorkflowExecution,
  WorkflowTemplate,
  WorkflowStats,
  WorkflowCreateParams,
  WorkflowUpdateParams,
  WorkflowQueryParams,
  WorkflowValidationResult,
  PaginatedResponse,
} from '@/types'

class WorkflowService extends BaseService {
  constructor() {
    super(import.meta.env.VITE_API_BASE_URL + '/workflows')
  }

  // 获取工作流列表
  async listWorkflows(params?: WorkflowQueryParams): Promise<PaginatedResponse<Workflow>> {
    return this.get('/', { params })
  }

  // 获取工作流详情
  async getWorkflow(id: string): Promise<Workflow> {
    return this.get(`/${id}`)
  }

  // 创建工作流
  async createWorkflow(params: WorkflowCreateParams): Promise<Workflow> {
    return this.post('/', params)
  }

  // 更新工作流
  async updateWorkflow(id: string, params: WorkflowUpdateParams): Promise<Workflow> {
    return this.put(`/${id}`, params)
  }

  // 删除工作流
  async deleteWorkflow(id: string): Promise<void> {
    return this.delete(`/${id}`)
  }

  // 批量删除工作流
  async deleteWorkflows(ids: string[]): Promise<void> {
    return this.post('/batch-delete', { ids })
  }

  // 复制工作流
  async duplicateWorkflow(
    id: string,
    params?: {
      name?: string
      description?: string
    }
  ): Promise<Workflow> {
    return this.post(`/${id}/duplicate`, params)
  }

  // 获取工作流统计
  async getWorkflowStats(params?: {
    dateFrom?: string
    dateTo?: string
  }): Promise<WorkflowStats> {
    return this.get('/stats', { params })
  }

  // 验证工作流
  async validateWorkflow(id: string): Promise<WorkflowValidationResult> {
    return this.post(`/${id}/validate`)
  }

  // 部署工作流
  async deployWorkflow(id: string): Promise<Workflow> {
    return this.post(`/${id}/deploy`)
  }

  // 停用工作流
  async deactivateWorkflow(id: string): Promise<Workflow> {
    return this.post(`/${id}/deactivate`)
  }

  // 获取工作流节点
  async getWorkflowNodes(workflowId: string): Promise<WorkflowNode[]> {
    return this.get(`/${workflowId}/nodes`)
  }

  // 添加工作流节点
  async addWorkflowNode(
    workflowId: string,
    node: Omit<WorkflowNode, 'id'>
  ): Promise<WorkflowNode> {
    return this.post(`/${workflowId}/nodes`, node)
  }

  // 更新工作流节点
  async updateWorkflowNode(
    workflowId: string,
    nodeId: string,
    node: Partial<WorkflowNode>
  ): Promise<WorkflowNode> {
    return this.put(`/${workflowId}/nodes/${nodeId}`, node)
  }

  // 删除工作流节点
  async deleteWorkflowNode(workflowId: string, nodeId: string): Promise<void> {
    return this.delete(`/${workflowId}/nodes/${nodeId}`)
  }

  // 获取工作流连接
  async getWorkflowEdges(workflowId: string): Promise<WorkflowEdge[]> {
    return this.get(`/${workflowId}/edges`)
  }

  // 添加工作流连接
  async addWorkflowEdge(
    workflowId: string,
    edge: Omit<WorkflowEdge, 'id'>
  ): Promise<WorkflowEdge> {
    return this.post(`/${workflowId}/edges`, edge)
  }

  // 更新工作流连接
  async updateWorkflowEdge(
    workflowId: string,
    edgeId: string,
    edge: Partial<WorkflowEdge>
  ): Promise<WorkflowEdge> {
    return this.put(`/${workflowId}/edges/${edgeId}`, edge)
  }

  // 删除工作流连接
  async deleteWorkflowEdge(workflowId: string, edgeId: string): Promise<void> {
    return this.delete(`/${workflowId}/edges/${edgeId}`)
  }

  // 执行工作流
  async executeWorkflow(
    id: string,
    params?: {
      input?: any
      variables?: Record<string, any>
      async?: boolean
    }
  ): Promise<WorkflowExecution> {
    return this.post(`/${id}/execute`, params)
  }

  // 获取工作流执行历史
  async getWorkflowExecutions(
    workflowId: string,
    params?: {
      page?: number
      pageSize?: number
      status?: string
      dateFrom?: string
      dateTo?: string
    }
  ): Promise<PaginatedResponse<WorkflowExecution>> {
    return this.get(`/${workflowId}/executions`, { params })
  }

  // 获取工作流执行详情
  async getWorkflowExecution(workflowId: string, executionId: string): Promise<WorkflowExecution> {
    return this.get(`/${workflowId}/executions/${executionId}`)
  }

  // 停止工作流执行
  async stopWorkflowExecution(workflowId: string, executionId: string): Promise<void> {
    return this.post(`/${workflowId}/executions/${executionId}/stop`)
  }

  // 暂停工作流执行
  async pauseWorkflowExecution(workflowId: string, executionId: string): Promise<void> {
    return this.post(`/${workflowId}/executions/${executionId}/pause`)
  }

  // 恢复工作流执行
  async resumeWorkflowExecution(workflowId: string, executionId: string): Promise<void> {
    return this.post(`/${workflowId}/executions/${executionId}/resume`)
  }

  // 获取工作流模板
  async getWorkflowTemplates(params?: {
    category?: string
    tags?: string[]
    search?: string
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<WorkflowTemplate>> {
    return this.get('/templates', { params })
  }

  // 获取工作流模板详情
  async getWorkflowTemplate(id: string): Promise<WorkflowTemplate> {
    return this.get(`/templates/${id}`)
  }

  // 从模板创建工作流
  async createWorkflowFromTemplate(
    templateId: string,
    params?: {
      name?: string
      description?: string
    }
  ): Promise<Workflow> {
    return this.post(`/templates/${templateId}/create`, params)
  }

  // 导出工作流
  async exportWorkflow(
    id: string,
    format: 'json' | 'yaml' | 'xml' = 'json'
  ): Promise<{ downloadUrl: string; filename: string }> {
    return this.get(`/${id}/export`, { params: { format } })
  }

  // 导入工作流
  async importWorkflow(file: File): Promise<Workflow> {
    return this.upload('/import', file)
  }

  // 获取工作流版本历史
  async getWorkflowVersions(id: string): Promise<any[]> {
    return this.get(`/${id}/versions`)
  }

  // 创建工作流版本
  async createWorkflowVersion(
    id: string,
    params?: {
      description?: string
      tags?: string[]
    }
  ): Promise<any> {
    return this.post(`/${id}/versions`, params)
  }

  // 恢复工作流版本
  async restoreWorkflowVersion(id: string, versionId: string): Promise<Workflow> {
    return this.post(`/${id}/versions/${versionId}/restore`)
  }

  // 获取工作流权限
  async getWorkflowPermissions(id: string): Promise<any[]> {
    return this.get(`/${id}/permissions`)
  }

  // 更新工作流权限
  async updateWorkflowPermissions(id: string, permissions: any[]): Promise<void> {
    return this.put(`/${id}/permissions`, { permissions })
  }

  // 获取工作流日志
  async getWorkflowLogs(
    workflowId: string,
    params?: {
      level?: 'debug' | 'info' | 'warn' | 'error'
      dateFrom?: string
      dateTo?: string
      page?: number
      pageSize?: number
    }
  ): Promise<PaginatedResponse<any>> {
    return this.get(`/${workflowId}/logs`, { params })
  }

  // 获取工作流指标
  async getWorkflowMetrics(
    workflowId: string,
    params?: {
      dateFrom?: string
      dateTo?: string
      granularity?: 'hour' | 'day' | 'week' | 'month'
    }
  ): Promise<any> {
    return this.get(`/${workflowId}/metrics`, { params })
  }

  // 测试工作流节点
  async testWorkflowNode(
    workflowId: string,
    nodeId: string,
    input: any
  ): Promise<{ output: any; logs: string[]; duration: number }> {
    return this.post(`/${workflowId}/nodes/${nodeId}/test`, { input })
  }

  // 获取节点类型定义
  async getNodeTypes(): Promise<any[]> {
    return this.get('/node-types')
  }

  // 获取节点类型详情
  async getNodeType(type: string): Promise<any> {
    return this.get(`/node-types/${type}`)
  }
}

export const workflowService = new WorkflowService()
export default workflowService