// 导出布局组件
export { default as AppLayout } from './AppLayout'
export { default as AppHeader } from './AppHeader'
export { default as AppSidebar } from './AppSidebar'
export { default as AppContent } from './AppContent'

// 重新导出常用组件
import AppLayout from './AppLayout'
import AppHeader from './AppHeader'
import AppSidebar from './AppSidebar'
import AppContent from './AppContent'

export const layoutComponents = {
  AppLayout,
  AppHeader,
  AppSidebar,
  AppContent,
}

export default layoutComponents