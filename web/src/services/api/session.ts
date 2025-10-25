import { BaseService } from './base'
import {
  Session,
  SessionDetail,
  SessionCreateParams,
  SessionUpdateParams,
  SessionQueryParams,
  SessionStats,
  SessionExportOptions,
  SessionBookmark,
  PaginatedResponse,
} from '@/types'

class SessionService extends BaseService {
  constructor() {
    super(import.meta.env.VITE_API_BASE_URL + '/sessions')
  }

  // 获取会话列表
  async listSessions(params?: SessionQueryParams): Promise<PaginatedResponse<Session>> {
    return this.get('/', { params })
  }

  // 获取会话详情
  async getSession(id: string): Promise<SessionDetail> {
    return this.get(`/${id}`)
  }

  // 创建会话
  async createSession(params: SessionCreateParams): Promise<Session> {
    return this.post('/', params)
  }

  // 更新会话
  async updateSession(id: string, params: SessionUpdateParams): Promise<Session> {
    return this.put(`/${id}`, params)
  }

  // 删除会话
  async deleteSession(id: string): Promise<void> {
    return this.delete(`/${id}`)
  }

  // 批量删除会话
  async deleteSessions(ids: string[]): Promise<void> {
    return this.post('/batch-delete', { ids })
  }

  // 暂停会话
  async pauseSession(id: string): Promise<Session> {
    return this.post(`/${id}/pause`)
  }

  // 恢复会话
  async resumeSession(id: string): Promise<Session> {
    return this.post(`/${id}/resume`)
  }

  // 停止会话
  async stopSession(id: string): Promise<Session> {
    return this.post(`/${id}/stop`)
  }

  // 获取会话统计
  async getSessionStats(params?: {
    dateFrom?: string
    dateTo?: string
  }): Promise<SessionStats> {
    return this.get('/stats', { params })
  }

  // 导出会话
  async exportSessions(
    options: SessionExportOptions
  ): Promise<{ downloadUrl: string; filename: string }> {
    return this.post('/export', options)
  }

  // 导入会话
  async importSessions(file: File): Promise<{ imported: number; errors: string[] }> {
    return this.upload('/import', file)
  }

  // 获取会话消息
  async getSessionMessages(
    sessionId: string,
    params?: {
      page?: number
      pageSize?: number
      search?: string
    }
  ): Promise<PaginatedResponse<any>> {
    return this.get(`/${sessionId}/messages`, { params })
  }

  // 发送消息到会话
  async sendMessage(
    sessionId: string,
    message: {
      content: string
      type?: 'text' | 'image' | 'file'
      metadata?: Record<string, any>
    }
  ): Promise<any> {
    return this.post(`/${sessionId}/messages`, message)
  }

  // 获取会话书签
  async getSessionBookmarks(sessionId: string): Promise<SessionBookmark[]> {
    return this.get(`/${sessionId}/bookmarks`)
  }

  // 添加会话书签
  async addSessionBookmark(
    sessionId: string,
    bookmark: {
      name: string
      description?: string
      messageId?: string
      tags?: string[]
    }
  ): Promise<SessionBookmark> {
    return this.post(`/${sessionId}/bookmarks`, bookmark)
  }

  // 删除会话书签
  async deleteSessionBookmark(sessionId: string, bookmarkId: string): Promise<void> {
    return this.delete(`/${sessionId}/bookmarks/${bookmarkId}`)
  }

  // 获取会话性能数据
  async getSessionPerformance(
    sessionId: string,
    params?: {
      dateFrom?: string
      dateTo?: string
    }
  ): Promise<any> {
    return this.get(`/${sessionId}/performance`, { params })
  }

  // 获取会话错误日志
  async getSessionErrors(
    sessionId: string,
    params?: {
      page?: number
      pageSize?: number
      severity?: 'low' | 'medium' | 'high' | 'critical'
      resolved?: boolean
    }
  ): Promise<PaginatedResponse<any>> {
    return this.get(`/${sessionId}/errors`, { params })
  }

  // 标记错误为已解决
  async resolveSessionError(sessionId: string, errorId: string): Promise<void> {
    return this.post(`/${sessionId}/errors/${errorId}/resolve`)
  }

  // 获取会话工作流信息
  async getSessionWorkflow(sessionId: string): Promise<any> {
    return this.get(`/${sessionId}/workflow`)
  }

  // 重新运行会话工作流
  async rerunSessionWorkflow(
    sessionId: string,
    params?: {
      fromNodeId?: string
      resetData?: boolean
    }
  ): Promise<any> {
    return this.post(`/${sessionId}/workflow/rerun`, params)
  }

  // 获取会话配置
  async getSessionConfig(sessionId: string): Promise<any> {
    return this.get(`/${sessionId}/config`)
  }

  // 更新会话配置
  async updateSessionConfig(sessionId: string, config: any): Promise<any> {
    return this.put(`/${sessionId}/config`, config)
  }

  // 克隆会话
  async cloneSession(
    id: string,
    params?: {
      name?: string
      description?: string
      includeMessages?: boolean
      includeConfig?: boolean
    }
  ): Promise<Session> {
    return this.post(`/${id}/clone`, params)
  }

  // 分享会话
  async shareSession(
    id: string,
    params?: {
      expiresAt?: string
      password?: string
      allowDownload?: boolean
    }
  ): Promise<{ shareUrl: string; shareId: string }> {
    return this.post(`/${id}/share`, params)
  }

  // 获取分享的会话
  async getSharedSession(shareId: string): Promise<SessionDetail> {
    return this.get(`/shared/${shareId}`)
  }

  // 搜索会话
  async searchSessions(params: {
    query: string
    filters?: {
      status?: string[]
      agentType?: string[]
      dateFrom?: string
      dateTo?: string
      tags?: string[]
    }
    sort?: {
      field: string
      order: 'asc' | 'desc'
    }
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<Session>> {
    return this.post('/search', params)
  }
}

export const sessionService = new SessionService()
export default sessionService