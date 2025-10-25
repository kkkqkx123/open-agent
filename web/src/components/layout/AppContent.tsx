import React from 'react'
import { Breadcrumb } from 'antd'
import { useLocation, Link } from 'react-router-dom'
import { useAppStore } from '@/stores'

interface AppContentProps {
  children: React.ReactNode
  showBreadcrumb?: boolean
  title?: string
  subtitle?: string
  extra?: React.ReactNode
}

const AppContent: React.FC<AppContentProps> = ({
  children,
  showBreadcrumb = true,
  title,
  subtitle,
  extra,
}) => {
  const location = useLocation()
  const { ui } = useAppStore()

  // 生成面包屑导航
  const generateBreadcrumb = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean)
    const breadcrumbItems = [
      {
        title: <Link to="/">首页</Link>,
      },
    ]

    // 路径映射
    const pathMap: Record<string, string> = {
      dashboard: '仪表板',
      workflows: '工作流',
      analytics: '性能分析',
      errors: '错误管理',
      history: '历史数据',
      config: '配置管理',
      sessions: '会话',
      templates: '模板库',
      executions: '执行历史',
      'costs': '成本分析',
      messages: '消息记录',
      bookmarks: '书签管理',
      agents: '代理配置',
      tools: '工具配置',
      security: '安全设置',
      team: '团队管理',
      help: '帮助中心',
    }

    let currentPath = ''
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`
      const isLast = index === pathSegments.length - 1
      
      if (pathMap[segment]) {
        breadcrumbItems.push({
          title: isLast ? (
            pathMap[segment]
          ) : (
            <Link to={currentPath}>{pathMap[segment]}</Link>
          ),
        })
      } else if (segment.match(/^[a-f0-9-]{36}$/i)) {
        // UUID路径，显示为详情
        breadcrumbItems.push({
          title: '详情',
        })
      }
    })

    return breadcrumbItems
  }

  return (
    <div className="app-content-wrapper">
      {/* 页面头部 */}
      <div className="content-header">
        {showBreadcrumb && (
          <Breadcrumb
            items={generateBreadcrumb()}
            className="content-breadcrumb"
          />
        )}
        
        {(title || subtitle || extra) && (
          <div className="content-title-section">
            <div className="content-title-info">
              {title && <h1 className="content-title">{title}</h1>}
              {subtitle && <p className="content-subtitle">{subtitle}</p>}
            </div>
            {extra && <div className="content-extra">{extra}</div>}
          </div>
        )}
      </div>

      {/* 页面内容 */}
      <div className="content-body">
        {children}
      </div>

      {/* 页面底部 */}
      <div className="content-footer">
        <div className="footer-info">
          <span className="footer-text">
            © 2024 模块化代理框架 - 版本 {import.meta.env.VITE_APP_VERSION || '1.0.0'}
          </span>
          <span className="footer-separator">|</span>
          <span className="footer-text">
            环境: {import.meta.env.VITE_APP_ENV || 'development'}
          </span>
          <span className="footer-separator">|</span>
          <span className="footer-text">
            主题: {ui.theme === 'light' ? '浅色' : '深色'}
          </span>
        </div>
      </div>
    </div>
  )
}

export default AppContent