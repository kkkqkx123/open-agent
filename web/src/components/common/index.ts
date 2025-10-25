// 导出通用组件
export { default as LoadingSpinner } from './LoadingSpinner'
export { default as ErrorBoundary } from './ErrorBoundary'
export { default as NotificationCenter } from './NotificationCenter'
export { default as UserMenu } from './UserMenu'

// 重新导出常用组件
import LoadingSpinner from './LoadingSpinner'
import ErrorBoundary from './ErrorBoundary'
import NotificationCenter from './NotificationCenter'
import UserMenu from './UserMenu'

export const commonComponents = {
  LoadingSpinner,
  ErrorBoundary,
  NotificationCenter,
  UserMenu,
}

export default commonComponents