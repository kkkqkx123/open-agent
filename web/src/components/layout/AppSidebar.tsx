import React from 'react'
import { Menu, Divider, Space, Badge } from 'antd'
import {
  DashboardOutlined,
  NodeIndexOutlined,
  SettingOutlined,
  BarChartOutlined,
  ExclamationCircleOutlined,
  HistoryOutlined,
  ControlOutlined,
  RocketOutlined,
  BranchesOutlined,
  ToolOutlined,
  BugOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  TeamOutlined,
  CloudOutlined,
  SafetyOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAppStore } from '@/stores'
import { formatStatus } from '@/utils'

const AppSidebar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { ui, sessions, workflows, realtime } = useAppStore()

  // 获取当前路径
  const currentPath = location.pathname

  // 统计数据
  const runningSessions = sessions.filter(s => s.status === 'running').length
  const activeWorkflows = workflows.filter(w => w.status === 'active').length

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/workflows',
      icon: <BranchesOutlined />,
      label: '工作流',
      children: [
        {
          key: '/workflows',
          icon: <NodeIndexOutlined />,
          label: (
            <Space>
              工作流列表
              {activeWorkflows > 0 && (
                <Badge count={activeWorkflows} size="small" />
              )}
            </Space>
          ),
        },
        {
          key: '/workflows/templates',
          icon: <FileTextOutlined />,
          label: '模板库',
        },
        {
          key: '/workflows/executions',
          icon: <RocketOutlined />,
          label: '执行历史',
        },
      ],
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: '性能分析',
      children: [
        {
          key: '/analytics',
          icon: <BarChartOutlined />,
          label: '性能概览',
        },
        {
          key: '/analytics/sessions',
          icon: <NodeIndexOutlined />,
          label: '会话分析',
        },
        {
          key: '/analytics/workflows',
          icon: <BranchesOutlined />,
          label: '工作流分析',
        },
        {
          key: '/analytics/costs',
          icon: <CloudOutlined />,
          label: '成本分析',
        },
      ],
    },
    {
      key: '/errors',
      icon: <ExclamationCircleOutlined />,
      label: (
        <Space>
          错误管理
          {/* 这里可以添加错误数量统计 */}
        </Space>
      ),
      children: [
        {
          key: '/errors',
          icon: <BugOutlined />,
          label: '错误列表',
        },
        {
          key: '/errors/analytics',
          icon: <BarChartOutlined />,
          label: '错误分析',
        },
      ],
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: '历史数据',
      children: [
        {
          key: '/history',
          icon: <ClockCircleOutlined />,
          label: (
            <Space>
              会话历史
              {runningSessions > 0 && (
                <Badge count={runningSessions} size="small" />
              )}
            </Space>
          ),
        },
        {
          key: '/history/messages',
          icon: <FileTextOutlined />,
          label: '消息记录',
        },
        {
          key: '/history/bookmarks',
          icon: <FileTextOutlined />,
          label: '书签管理',
        },
      ],
    },
    {
      key: '/config',
      icon: <SettingOutlined />,
      label: '配置管理',
      children: [
        {
          key: '/config',
          icon: <ControlOutlined />,
          label: '系统配置',
        },
        {
          key: '/config/agents',
          icon: <RobotOutlined />,
          label: '代理配置',
        },
        {
          key: '/config/tools',
          icon: <ToolOutlined />,
          label: '工具配置',
        },
        {
          key: '/config/security',
          icon: <SafetyOutlined />,
          label: '安全设置',
        },
      ],
    },
  ]

  // 底部菜单项
  const bottomMenuItems = [
    {
      key: '/team',
      icon: <TeamOutlined />,
      label: '团队管理',
    },
    {
      key: '/help',
      icon: <QuestionCircleOutlined />,
      label: '帮助中心',
    },
  ]

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  // 获取选中的菜单项
  const getSelectedKeys = () => {
    // 精确匹配
    if (menuItems.some(item => item.key === currentPath)) {
      return [currentPath]
    }

    // 子菜单匹配
    for (const item of menuItems) {
      if (item.children) {
        for (const child of item.children) {
          if (child.key === currentPath) {
            return [child.key]
          }
        }
      }
    }

    // 父菜单匹配（当前路径是子路径）
    for (const item of menuItems) {
      if (currentPath.startsWith(item.key + '/')) {
        return [item.key]
      }
    }

    return ['/dashboard']
  }

  // 获取展开的菜单项
  const getOpenKeys = () => {
    const openKeys: string[] = []
    
    for (const item of menuItems) {
      if (item.children) {
        for (const child of item.children) {
          if (currentPath.startsWith(child.key)) {
            openKeys.push(item.key)
            break
          }
        }
      }
    }
    
    return openKeys
  }

  return (
    <div className="app-sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <RocketOutlined className="logo-icon" />
          <span className="logo-text">MAAF</span>
        </div>
        
        {/* 连接状态指示器 */}
        <div className="connection-status">
          <div
            className={`status-dot ${realtime.connected ? 'connected' : 'disconnected'}`}
          />
          <span className="status-text">
            {realtime.connected ? '已连接' : '未连接'}
          </span>
        </div>
      </div>

      <div className="sidebar-content">
        <Menu
          mode="inline"
          selectedKeys={getSelectedKeys()}
          defaultOpenKeys={getOpenKeys()}
          items={menuItems}
          onClick={handleMenuClick}
          className="main-menu"
        />

        <Divider style={{ margin: '12px 0' }} />

        <Menu
          mode="inline"
          selectedKeys={[]}
          items={bottomMenuItems}
          onClick={handleMenuClick}
          className="bottom-menu"
        />
      </div>

      <div className="sidebar-footer">
        <div className="system-info">
          <div className="info-item">
            <span className="label">版本:</span>
            <span className="value">v1.0.0</span>
          </div>
          <div className="info-item">
            <span className="label">环境:</span>
            <span className="value">
              {import.meta.env.VITE_APP_ENV || 'development'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AppSidebar