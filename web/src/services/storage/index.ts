import { Session, Workflow, Notification } from '@/types'

// 存储键名常量
const STORAGE_KEYS = {
  TOKEN: 'token',
  USER: 'user',
  THEME: 'theme',
  LANGUAGE: 'language',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  RECENT_SESSIONS: 'recent_sessions',
  RECENT_WORKFLOWS: 'recent_workflows',
  BOOKMARKED_SESSIONS: 'bookmarked_sessions',
  NOTIFICATIONS: 'notifications',
  PREFERENCES: 'preferences',
  CACHE: 'cache_',
} as const

// 存储服务类
class StorageService {
  // 设置本地存储
  private setItem(key: string, value: any): void {
    try {
      const serializedValue = JSON.stringify(value)
      localStorage.setItem(key, serializedValue)
    } catch (error) {
      console.error('设置本地存储失败:', error)
    }
  }

  // 获取本地存储
  private getItem<T>(key: string, defaultValue?: T): T | null {
    try {
      const item = localStorage.getItem(key)
      if (item === null) {
        return defaultValue || null
      }
      return JSON.parse(item)
    } catch (error) {
      console.error('获取本地存储失败:', error)
      return defaultValue || null
    }
  }

  // 删除本地存储
  private removeItem(key: string): void {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('删除本地存储失败:', error)
    }
  }

  // 清空本地存储
  private clear(): void {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('清空本地存储失败:', error)
    }
  }

  // 认证相关
  setToken(token: string): void {
    this.setItem(STORAGE_KEYS.TOKEN, token)
  }

  getToken(): string | null {
    return this.getItem(STORAGE_KEYS.TOKEN)
  }

  removeToken(): void {
    this.removeItem(STORAGE_KEYS.TOKEN)
  }

  // 用户信息
  setUser(user: any): void {
    this.setItem(STORAGE_KEYS.USER, user)
  }

  getUser(): any | null {
    return this.getItem(STORAGE_KEYS.USER)
  }

  removeUser(): void {
    this.removeItem(STORAGE_KEYS.USER)
  }

  // 主题设置
  setTheme(theme: 'light' | 'dark'): void {
    this.setItem(STORAGE_KEYS.THEME, theme)
  }

  getTheme(): 'light' | 'dark' {
    return this.getItem(STORAGE_KEYS.THEME, 'light') || 'light'
  }

  // 语言设置
  setLanguage(language: string): void {
    this.setItem(STORAGE_KEYS.LANGUAGE, language)
  }

  getLanguage(): string {
    return this.getItem(STORAGE_KEYS.LANGUAGE, 'zh-CN') || 'zh-CN'
  }

  // 侧边栏状态
  setSidebarCollapsed(collapsed: boolean): void {
    this.setItem(STORAGE_KEYS.SIDEBAR_COLLAPSED, collapsed)
  }

  getSidebarCollapsed(): boolean {
    return this.getItem(STORAGE_KEYS.SIDEBAR_COLLAPSED, false) || false
  }

  // 最近会话
  setRecentSessions(sessions: Session[]): void {
    this.setItem(STORAGE_KEYS.RECENT_SESSIONS, sessions.slice(0, 10)) // 只保留最近10个
  }

  getRecentSessions(): Session[] {
    return this.getItem(STORAGE_KEYS.RECENT_SESSIONS, [])
  }

  addRecentSession(session: Session): void {
    const recentSessions = this.getRecentSessions()
    const filteredSessions = recentSessions.filter(s => s.id !== session.id)
    this.setRecentSessions([session, ...filteredSessions])
  }

  removeRecentSession(sessionId: string): void {
    const recentSessions = this.getRecentSessions()
    const filteredSessions = recentSessions.filter(s => s.id !== sessionId)
    this.setRecentSessions(filteredSessions)
  }

  // 最近工作流
  setRecentWorkflows(workflows: Workflow[]): void {
    this.setItem(STORAGE_KEYS.RECENT_WORKFLOWS, workflows.slice(0, 10))
  }

  getRecentWorkflows(): Workflow[] {
    return this.getItem(STORAGE_KEYS.RECENT_WORKFLOWS, [])
  }

  addRecentWorkflow(workflow: Workflow): void {
    const recentWorkflows = this.getRecentWorkflows()
    const filteredWorkflows = recentWorkflows.filter(w => w.id !== workflow.id)
    this.setRecentWorkflows([workflow, ...filteredWorkflows])
  }

  removeRecentWorkflow(workflowId: string): void {
    const recentWorkflows = this.getRecentWorkflows()
    const filteredWorkflows = recentWorkflows.filter(w => w.id !== workflowId)
    this.setRecentWorkflows(filteredWorkflows)
  }

  // 书签会话
  setBookmarkedSessions(sessionIds: string[]): void {
    this.setItem(STORAGE_KEYS.BOOKMARKED_SESSIONS, sessionIds)
  }

  getBookmarkedSessions(): string[] {
    return this.getItem(STORAGE_KEYS.BOOKMARKED_SESSIONS, [])
  }

  addBookmarkedSession(sessionId: string): void {
    const bookmarkedSessions = this.getBookmarkedSessions()
    if (!bookmarkedSessions.includes(sessionId)) {
      this.setBookmarkedSessions([...bookmarkedSessions, sessionId])
    }
  }

  removeBookmarkedSession(sessionId: string): void {
    const bookmarkedSessions = this.getBookmarkedSessions()
    const filteredSessions = bookmarkedSessions.filter(id => id !== sessionId)
    this.setBookmarkedSessions(filteredSessions)
  }

  // 通知
  setNotifications(notifications: Notification[]): void {
    this.setItem(STORAGE_KEYS.NOTIFICATIONS, notifications.slice(0, 50)) // 只保留最近50个
  }

  getNotifications(): Notification[] {
    return this.getItem(STORAGE_KEYS.NOTIFICATIONS, [])
  }

  addNotification(notification: Notification): void {
    const notifications = this.getNotifications()
    this.setNotifications([notification, ...notifications])
  }

  removeNotification(notificationId: string): void {
    const notifications = this.getNotifications()
    const filteredNotifications = notifications.filter(n => n.id !== notificationId)
    this.setNotifications(filteredNotifications)
  }

  clearNotifications(): void {
    this.removeItem(STORAGE_KEYS.NOTIFICATIONS)
  }

  // 用户偏好设置
  setPreferences(preferences: Record<string, any>): void {
    this.setItem(STORAGE_KEYS.PREFERENCES, preferences)
  }

  getPreferences(): Record<string, any> {
    return this.getItem(STORAGE_KEYS.PREFERENCES, {})
  }

  updatePreferences(updates: Record<string, any>): void {
    const preferences = this.getPreferences()
    this.setPreferences({ ...preferences, ...updates })
  }

  // 缓存管理
  setCache(key: string, data: any, ttl?: number): void {
    const cacheKey = STORAGE_KEYS.CACHE + key
    const cacheData = {
      data,
      timestamp: Date.now(),
      ttl: ttl || 3600000, // 默认1小时
    }
    this.setItem(cacheKey, cacheData)
  }

  getCache(key: string): any | null {
    const cacheKey = STORAGE_KEYS.CACHE + key
    const cacheData = this.getItem(cacheKey)
    
    if (!cacheData) {
      return null
    }

    const { data, timestamp, ttl } = cacheData
    const isExpired = Date.now() - timestamp > ttl

    if (isExpired) {
      this.removeItem(cacheKey)
      return null
    }

    return data
  }

  removeCache(key: string): void {
    const cacheKey = STORAGE_KEYS.CACHE + key
    this.removeItem(cacheKey)
  }

  clearCache(): void {
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith(STORAGE_KEYS.CACHE)) {
        this.removeItem(key)
      }
    })
  }

  // 清理过期缓存
  cleanExpiredCache(): void {
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith(STORAGE_KEYS.CACHE)) {
        const cacheData = this.getItem(key)
        if (cacheData && cacheData.ttl) {
          const isExpired = Date.now() - cacheData.timestamp > cacheData.ttl
          if (isExpired) {
            this.removeItem(key)
          }
        }
      }
    })
  }

  // 获取存储使用情况
  getStorageUsage(): { used: number; total: number; percentage: number } {
    let used = 0
    for (let key in localStorage) {
      if (localStorage.hasOwnProperty(key)) {
        used += localStorage[key].length + key.length
      }
    }
    
    // 假设总容量为5MB
    const total = 5 * 1024 * 1024
    const percentage = (used / total) * 100

    return { used, total, percentage }
  }

  // 导出数据
  exportData(): Record<string, any> {
    const data: Record<string, any> = {}
    Object.keys(STORAGE_KEYS).forEach(key => {
      const storageKey = STORAGE_KEYS[key as keyof typeof STORAGE_KEYS]
      const value = this.getItem(storageKey)
      if (value !== null) {
        data[key] = value
      }
    })
    return data
  }

  // 导入数据
  importData(data: Record<string, any>): void {
    Object.keys(data).forEach(key => {
      const storageKey = STORAGE_KEYS[key as keyof typeof STORAGE_KEYS]
      if (storageKey) {
        this.setItem(storageKey, data[key])
      }
    })
  }

  // 重置所有数据
  reset(): void {
    this.clear()
  }
}

export const storageService = new StorageService()
export default storageService