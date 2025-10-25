import React, { useState } from 'react'
import { Layout, Button, Space, Dropdown, Badge, Avatar, Tooltip, Switch, Input } from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  SearchOutlined,
  QuestionCircleOutlined,
  GithubOutlined,
  GlobalOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '@/stores'
import NotificationCenter from '../common/NotificationCenter'
import UserMenu from '../common/UserMenu'

const { Header } = Layout
const { Search } = Input

const AppHeader: React.FC = () => {
  const navigate = useNavigate()
  const {
    ui,
    user,
    notifications,
    toggleSidebar,
    setTheme,
    removeNotification,
    logout,
  } = useAppStore()

  const [searchVisible, setSearchVisible] = useState(false)
  const [notificationVisible, setNotificationVisible] = useState(false)
  const [userMenuVisible, setUserMenuVisible] = useState(false)

  // 未读通知数量
  const unreadCount = notifications.filter(n => !n.read).length

  // 处理搜索
  const handleSearch = (value: string) => {
    if (value.trim()) {
      navigate(`/search?q=${encodeURIComponent(value.trim())}`)
    }
    setSearchVisible(false)
  }

  // 处理通知点击
  const handleNotificationClick = () => {
    setNotificationVisible(true)
  }

  // 处理用户菜单点击
  const handleUserMenuClick = () => {
    setUserMenuVisible(true)
  }

  // 处理主题切换
  const handleThemeChange = (checked: boolean) => {
    setTheme(checked ? 'dark' : 'light')
  }

  // 快速操作菜单
  const quickActionsMenuItems = [
    {
      key: 'new-session',
      label: '新建会话',
      icon: <UserOutlined />,
      onClick: () => navigate('/sessions/new'),
    },
    {
      key: 'new-workflow',
      label: '新建工作流',
      icon: <SettingOutlined />,
      onClick: () => navigate('/workflows/new'),
    },
    {
      key: 'help',
      label: '帮助中心',
      icon: <QuestionCircleOutlined />,
      onClick: () => window.open('/help', '_blank'),
    },
    {
      key: 'github',
      label: 'GitHub',
      icon: <GithubOutlined />,
      onClick: () => window.open('https://github.com/your-repo', '_blank'),
    },
  ]

  return (
    <>
      <Header className="app-header">
        <div className="header-left">
          <Button
            type="text"
            icon={ui.sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={toggleSidebar}
            className="sidebar-toggle"
          />
          
          {searchVisible ? (
            <Search
              placeholder="搜索..."
              allowClear
              autoFocus
              style={{ width: 300 }}
              onSearch={handleSearch}
              onBlur={() => setSearchVisible(false)}
            />
          ) : (
            <Button
              type="text"
              icon={<SearchOutlined />}
              onClick={() => setSearchVisible(true)}
              className="search-button"
            />
          )}
        </div>

        <div className="header-center">
          <div className="app-title">
            <span className="title-text">模块化代理框架</span>
            <span className="version-text">v1.0.0</span>
          </div>
        </div>

        <div className="header-right">
          <Space size="middle">
            {/* 主题切换 */}
            <Tooltip title={ui.theme === 'light' ? '切换到深色模式' : '切换到浅色模式'}>
              <Switch
                checked={ui.theme === 'dark'}
                onChange={handleThemeChange}
                checkedChildren={<BulbOutlined />}
                unCheckedChildren={<GlobalOutlined />}
              />
            </Tooltip>

            {/* 快速操作 */}
            <Dropdown
              menu={{ items: quickActionsMenuItems }}
              placement="bottomRight"
              trigger={['click']}
            >
              <Button type="text" icon={<SettingOutlined />} />
            </Dropdown>

            {/* 通知中心 */}
            <Tooltip title="通知中心">
              <Badge count={unreadCount} size="small">
                <Button
                  type="text"
                  icon={<BellOutlined />}
                  onClick={handleNotificationClick}
                />
              </Badge>
            </Tooltip>

            {/* 用户菜单 */}
            <Tooltip title="用户菜单">
              <Button
                type="text"
                icon={
                  <Avatar
                    size="small"
                    src={user?.avatar}
                    icon={<UserOutlined />}
                  />
                }
                onClick={handleUserMenuClick}
              />
            </Tooltip>
          </Space>
        </div>
      </Header>

      {/* 通知中心抽屉 */}
      <NotificationCenter
        open={notificationVisible}
        onClose={() => setNotificationVisible(false)}
        onRemoveNotification={removeNotification}
      />

      {/* 用户菜单抽屉 */}
      <UserMenu
        open={userMenuVisible}
        onClose={() => setUserMenuVisible(false)}
        user={user}
        onLogout={logout}
      />
    </>
  )
}

export default AppHeader