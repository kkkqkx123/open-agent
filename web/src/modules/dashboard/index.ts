// 导出仪表板模块组件
export { default as Dashboard } from './Dashboard'
export { default as RecentSessions } from './RecentSessions'
export { default as SystemStatus } from './SystemStatus'
export { default as QuickActions } from './QuickActions'
export { default as ActivityFeed } from './ActivityFeed'

// 重新导出常用组件
import Dashboard from './Dashboard'
import RecentSessions from './RecentSessions'
import SystemStatus from './SystemStatus'
import QuickActions from './QuickActions'
import ActivityFeed from './ActivityFeed'

export const dashboardComponents = {
  Dashboard,
  RecentSessions,
  SystemStatus,
  QuickActions,
  ActivityFeed,
}

export default dashboardComponents