import React from 'react'
import {
  Drawer,
  List,
  Avatar,
  Button,
  Space,
  Divider,
  Typography,
  Tag,
  Switch,
  Tooltip,
} from 'antd'
import {
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  EditOutlined,
  SecurityScanOutlined,
  BellOutlined,
  GlobalOutlined,
  BulbOutlined,
  QuestionCircleOutlined,
  GithubOutlined,
  TeamOutlined,
  CrownOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '@/stores'

const { Title, Text } = Typography

interface UserMenuProps {
  open: boolean
  onClose: () => void
  user: any
  onLogout: () => void
}

const UserMenu: React.FC<UserMenuProps> = ({
  open,
  onClose,
  user,
  onLogout,
}) => {
  const navigate = useNavigate()
  const { ui, setTheme, setLanguage } = useAppStore()

  // 用户菜单项
  const menuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      title: '个人资料',
      description: '查看和编辑个人信息',
      onClick: () => {
        navigate('/profile')
        onClose()
      },
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      title: '账户设置',
      description: '管理账户偏好设置',
      onClick: () => {
        navigate('/settings')
        onClose()
      },
    },
    {
      key: 'security',
      icon: <SecurityScanOutlined />,
      title: '安全设置',
      description: '密码和安全选项',
      onClick: () => {
        navigate('/security')
        onClose()
      },
    },
    {
      key: 'notifications',
      icon: <BellOutlined />,
      title: '通知设置',
      description: '管理通知偏好',
      onClick: () => {
        navigate('/notifications')
        onClose()
      },
    },
  ]

  // 系统设置项
  const systemItems = [
    {
      key: 'theme',
      icon: <BulbOutlined />,
      title: '主题模式',
      description: ui.theme === 'light' ? '浅色模式' : '深色模式',
      action: (
        <Switch
          checked={ui.theme === 'dark'}
          onChange={(checked) => setTheme(checked ? 'dark' : 'light')}
          checkedChildren={<BulbOutlined />}
          unCheckedChildren={<GlobalOutlined />}
        />
      ),
    },
    {
      key: 'language',
      icon: <GlobalOutlined />,
      title: '语言设置',
      description: ui.language === 'zh-CN' ? '简体中文' : 'English',
      action: (
        <Switch
          checked={ui.language === 'en-US'}
          onChange={(checked) => setLanguage(checked ? 'en-US' : 'zh-CN')}
          checkedChildren="EN"
          unCheckedChildren="中"
        />
      ),
    },
  ]

  // 其他选项
  const otherItems = [
    {
      key: 'help',
      icon: <QuestionCircleOutlined />,
      title: '帮助中心',
      description: '获取帮助和支持',
      onClick: () => {
        window.open('/help', '_blank')
        onClose()
      },
    },
    {
      key: 'github',
      icon: <GithubOutlined />,
      title: 'GitHub',
      description: '查看源代码',
      onClick: () => {
        window.open('https://github.com/your-repo', '_blank')
        onClose()
      },
    },
    {
      key: 'team',
      icon: <TeamOutlined />,
      title: '团队管理',
      description: '管理团队成员',
      onClick: () => {
        navigate('/team')
        onClose()
      },
    },
  ]

  // 渲染菜单项
  const renderMenuItem = (item: any) => (
    <List.Item
      key={item.key}
      onClick={item.onClick}
      className="user-menu-item"
      actions={[item.action]}
    >
      <List.Item.Meta
        avatar={<Avatar icon={item.icon} />}
        title={
          <Space>
            {item.title}
            {item.key === 'profile' && user?.role === 'admin' && (
              <Tag icon={<CrownOutlined />} color="gold">
                管理员
              </Tag>
            )}
          </Space>
        }
        description={item.description}
      />
    </List.Item>
  )

  return (
    <Drawer
      title={
        <div className="user-menu-header">
          <Space>
            <Avatar
              size="large"
              src={user?.avatar}
              icon={<UserOutlined />}
            />
            <div>
              <Title level={5} style={{ margin: 0 }}>
                {user?.name || '用户'}
              </Title>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {user?.email || 'user@example.com'}
              </Text>
            </div>
          </Space>
        </div>
      }
      placement="right"
      width={360}
      open={open}
      onClose={onClose}
      className="user-menu-drawer"
      extra={
        <Button
          type="text"
          icon={<EditOutlined />}
          onClick={() => {
            navigate('/profile')
            onClose()
          }}
        >
          编辑
        </Button>
      }
    >
      <div className="user-menu-content">
        {/* 用户信息统计 */}
        <div className="user-stats">
          <div className="stat-item">
            <div className="stat-value">{user?.sessions || 0}</div>
            <div className="stat-label">会话数</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{user?.workflows || 0}</div>
            <div className="stat-label">工作流</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{user?.joinDays || 0}</div>
            <div className="stat-label">加入天数</div>
          </div>
        </div>

        <Divider style={{ margin: '16px 0' }} />

        {/* 用户菜单 */}
        <div className="menu-section">
          <Title level={5}>账户</Title>
          <List
            dataSource={menuItems}
            renderItem={renderMenuItem}
            size="small"
          />
        </div>

        <Divider style={{ margin: '16px 0' }} />

        {/* 系统设置 */}
        <div className="menu-section">
          <Title level={5}>系统设置</Title>
          <List
            dataSource={systemItems}
            renderItem={renderMenuItem}
            size="small"
          />
        </div>

        <Divider style={{ margin: '16px 0' }} />

        {/* 其他选项 */}
        <div className="menu-section">
          <Title level={5}>其他</Title>
          <List
            dataSource={otherItems}
            renderItem={renderMenuItem}
            size="small"
          />
        </div>

        <Divider style={{ margin: '16px 0' }} />

        {/* 登出按钮 */}
        <div className="menu-section">
          <Button
            type="primary"
            danger
            block
            icon={<LogoutOutlined />}
            onClick={() => {
              onLogout()
              onClose()
            }}
          >
            退出登录
          </Button>
        </div>

        {/* 版本信息 */}
        <div className="version-info">
          <Text type="secondary" style={{ fontSize: 12 }}>
            版本 {import.meta.env.VITE_APP_VERSION || '1.0.0'}
          </Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            环境: {import.meta.env.VITE_APP_ENV || 'development'}
          </Text>
        </div>
      </div>
    </Drawer>
  )
}

export default UserMenu