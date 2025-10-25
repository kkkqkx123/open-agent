import { BaseService } from './base'
import { PerformanceMetrics, SystemStatus } from '@/types'

class AnalyticsService extends BaseService {
  constructor() {
    super(import.meta.env.VITE_API_BASE_URL + '/analytics')
  }

  // 获取性能数据
  async getPerformanceData(params: {
    startDate: string
    endDate: string
    granularity?: 'hour' | 'day' | 'week' | 'month'
    metrics?: string[]
  }): Promise<{
    responseTimeTrend: any[]
    throughputTrend: any[]
    errorRateTrend: any[]
    costTrend: any[]
    summary: {
      averageResponseTime: number
      totalRequests: number
      errorRate: number
      totalCost: number
    }
  }> {
    return this.get('/performance', { params })
  }

  // 获取错误分析数据
  async getErrorAnalysis(params: {
    startDate: string
    endDate: string
    groupBy?: 'type' | 'severity' | 'component' | 'time'
  }): Promise<{
    errorDistribution: any[]
    errorTrend: any[]
    topErrors: any[]
    summary: {
      totalErrors: number
      errorRate: number
      criticalErrors: number
      resolvedErrors: number
    }
  }> {
    return this.get('/errors', { params })
  }

  // 获取成本分析数据
  async getCostAnalysis(params: {
    startDate: string
    endDate: string
    groupBy?: 'service' | 'model' | 'workflow' | 'user'
  }): Promise<{
    costTrend: any[]
    costDistribution: any[]
    costBreakdown: any[]
    summary: {
      totalCost: number
      averageDailyCost: number
      costGrowth: number
      projectedMonthlyCost: number
    }
  }> {
    return this.get('/costs', { params })
  }

  // 获取使用情况统计
  async getUsageStats(params: {
    startDate: string
    endDate: string
    groupBy?: 'user' | 'workflow' | 'feature' | 'time'
  }): Promise<{
    usageTrend: any[]
    usageDistribution: any[]
    topUsers: any[]
    topWorkflows: any[]
    summary: {
      totalUsers: number
      activeUsers: number
      totalSessions: number
      averageSessionDuration: number
    }
  }> {
    return this.get('/usage', { params })
  }

  // 获取系统状态
  async getSystemStatus(): Promise<SystemStatus> {
    return this.get('/system-status')
  }

  // 获取实时指标
  async getRealTimeMetrics(): Promise<{
    responseTime: number
    throughput: number
    errorRate: number
    activeUsers: number
    activeSessions: number
    memoryUsage: number
    cpuUsage: number
    timestamp: string
  }> {
    return this.get('/realtime')
  }

  // 获取会话分析
  async getSessionAnalytics(params: {
    startDate: string
    endDate: string
    filters?: {
      agentType?: string[]
      status?: string[]
      userId?: string
    }
  }): Promise<{
    sessionTrend: any[]
    sessionDistribution: any[]
    sessionDuration: any[]
    messageStats: any[]
    summary: {
      totalSessions: number
      averageDuration: number
      completionRate: number
      totalMessages: number
    }
  }> {
    return this.get('/sessions', { params })
  }

  // 获取工作流分析
  async getWorkflowAnalytics(params: {
    startDate: string
    endDate: string
    filters?: {
      status?: string[]
      category?: string[]
    }
  }): Promise<{
    executionTrend: any[]
    successRate: any[]
    executionTime: any[]
    topWorkflows: any[]
    summary: {
      totalExecutions: number
      successRate: number
      averageExecutionTime: number
      totalWorkflows: number
    }
  }> {
    return this.get('/workflows', { params })
  }

  // 获取模型使用分析
  async getModelAnalytics(params: {
    startDate: string
    endDate: string
    models?: string[]
  }): Promise<{
    modelUsage: any[]
    tokenUsage: any[]
    costByModel: any[]
    performanceByModel: any[]
    summary: {
      totalTokens: number
      totalCost: number
      averageResponseTime: number
      topModel: string
    }
  }> {
    return this.get('/models', { params })
  }

  // 获取工具使用分析
  async getToolAnalytics(params: {
    startDate: string
    endDate: string
    tools?: string[]
  }): Promise<{
    toolUsage: any[]
    toolSuccessRate: any[]
    toolExecutionTime: any[]
    topTools: any[]
    summary: {
      totalToolCalls: number
      successRate: number
      averageExecutionTime: number
      topTool: string
    }
  }> {
    return this.get('/tools', { params })
  }

  // 获取用户行为分析
  async getUserBehaviorAnalytics(params: {
    startDate: string
    endDate: string
    userIds?: string[]
  }): Promise<{
    userActivity: any[]
    featureUsage: any[]
    userJourney: any[]
    retentionData: any[]
    summary: {
      totalUsers: number
      activeUsers: number
      newUsers: number
      retentionRate: number
    }
  }> {
    return this.get('/user-behavior', { params })
  }

  // 获取自定义报告
  async getCustomReport(reportId: string, params?: any): Promise<any> {
    return this.get(`/reports/${reportId}`, { params })
  }

  // 创建自定义报告
  async createCustomReport(report: {
    name: string
    description?: string
    config: {
      metrics: string[]
      filters: any
      groupBy?: string
      timeRange: {
        start: string
        end: string
      }
    }
    schedule?: {
      enabled: boolean
      frequency: 'daily' | 'weekly' | 'monthly'
      recipients: string[]
    }
  }): Promise<any> {
    return this.post('/reports', report)
  }

  // 导出分析数据
  async exportAnalytics(params: {
    type: 'performance' | 'errors' | 'costs' | 'usage'
    format: 'csv' | 'excel' | 'pdf' | 'json'
    dateRange: {
      start: string
      end: string
    }
    filters?: any
  }): Promise<{ downloadUrl: string; filename: string }> {
    return this.post('/export', params)
  }

  // 获取预测分析
  async getPredictiveAnalytics(params: {
    type: 'usage' | 'cost' | 'errors'
    horizon: '7d' | '30d' | '90d'
  }): Promise<{
    predictions: any[]
    confidence: number
    accuracy: number
    insights: string[]
  }> {
    return this.get('/predictive', { params })
  }

  // 获取异常检测结果
  async getAnomalyDetection(params: {
    startDate: string
    endDate: string
    metrics: string[]
    sensitivity?: 'low' | 'medium' | 'high'
  }): Promise<{
    anomalies: any[]
    summary: {
      totalAnomalies: number
      severity: 'low' | 'medium' | 'high'
      affectedMetrics: string[]
    }
  }> {
    return this.get('/anomalies', { params })
  }

  // 获取性能基准
  async getPerformanceBenchmarks(): Promise<{
    benchmarks: any[]
    comparisons: any[]
    recommendations: string[]
  }> {
    return this.get('/benchmarks')
  }

  // 获取健康检查结果
  async getHealthCheck(): Promise<{
    status: 'healthy' | 'warning' | 'critical'
    checks: any[]
    score: number
    lastCheck: string
  }> {
    return this.get('/health')
  }
}

export const analyticsService = new AnalyticsService()
export default analyticsService