import React from 'react'
import { Row, Col, Button, Space, Typography } from 'antd'
import {
  PlusOutlined,
  BranchesOutlined,
  PlayCircleOutlined,
  SettingOutlined,
  FileTextOutlined,
  BarChartOutlined,
  BugOutlined,
  HistoryOutlined,
  RocketOutlined,
  ToolOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title } = Typography

const QuickActions: React.FC = () => {
  const navigate = useNavigate()

  // 快速操作配置
  const quickActions = [
    {
      key: 'new-session',
      title: '新建会话',
      description: '创建新的对话会话',
      icon: <PlusOutlined />,
      color: '#1890ff',
      onClick: () => navigate('/sessions/new'),
    },
    {
      key: 'new-workflow',
      title: '新建工作流',
      description: '创建新的工作流',
      icon: <BranchesOutlined />,
      color: '#52c41a',
      onClick: () => navigate('/workflows/new'),
    },
    {
      key: 'run-workflow',
      title: '执行工作流',
      description: '运行现有工作流',
      icon: <PlayCircleOutlined />,
      color: '#faad14',
      onClick: () => navigate('/workflows'),
    },
    {
      key: 'view-analytics',
      title: '查看分析',
      description: '查看性能分析',
      icon: <BarChartOutlined />,
      color: '#722ed1',
      onClick: () => navigate('/analytics'),
    },
    {
      key: 'check-errors',
      title: '检查错误',
      description: '查看系统错误',
      icon: <BugOutlined />,
      color: '#ff4d4f',
      onClick: () => navigate('/errors'),
    },
    {
      key: 'view-history',
      title: '历史记录',
      description: '查看历史数据',
      icon: <HistoryOutlined />,
      color: '#13c2c2',
      onClick: () => navigate('/history'),
    },
    {
      key: 'system-config',
      title: '系统配置',
      description: '管理系统配置',
      icon: <SettingOutlined />,
      color: '#eb2f96',
      onClick: () => navigate('/config'),
    },
    {
      key: 'view-docs',
      title: '查看文档',
      description: '查看帮助文档',
      icon: <FileTextOutlined />,
      color: '#595959',
      onClick: () => window.open('/help', '_blank'),
    },
  ]

  return (
    <div className="quick-actions">
      <Title level={5}>快速操作</Title>
      <Row gutter={[16, 16]}>
        {quickActions.map((action) => (
          <Col xs={24} sm={12} md={8} lg={6} key={action.key}>
            <Button
              className="quick-action-button"
              style={{
                height: 'auto',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                textAlign: 'center',
                border: `1px solid ${action.color}20`,
                borderRadius: '8px',
                transition: 'all 0.3s ease',
              }}
              onClick={action.onClick}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.boxShadow = `0 4px 12px ${action.color}30`
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              <div
                className="action-icon"
                style={{
                  fontSize: '24px',
                  color: action.color,
                  marginBottom: '8px',
                }}
              >
                {action.icon}
              </div>
              <div className="action-content">
                <div
                  className="action-title"
                  style={{
                    fontWeight: 600,
                    marginBottom: '4px',
                    color: '#262626',
                  }}
                >
                  {action.title}
                </div>
                <div
                  className="action-description"
                  style={{
                    fontSize: '12px',
                    color: '#8c8c8c',
                    lineHeight: '1.4',
                  }}
                >
                  {action.description}
                </div>
              </div>
            </Button>
          </Col>
        ))}
      </Row>

      {/* 常用工具 */}
      <div style={{ marginTop: 24 }}>
        <Title level={5}>常用工具</Title>
        <Space wrap>
          <Button
            icon={<RocketOutlined />}
            onClick={() => navigate('/workflows/templates')}
          >
            工作流模板
          </Button>
          <Button
            icon={<ToolOutlined />}
            onClick={() => navigate('/config/tools')}
          >
            工具配置
          </Button>
          <Button
            icon={<BarChartOutlined />}
            onClick={() => navigate('/analytics/costs')}
          >
            成本分析
          </Button>
          <Button
            icon={<SettingOutlined />}
            onClick={() => navigate('/config/security')}
          >
            安全设置
          </Button>
        </Space>
      </div>
    </div>
  )
}

export default QuickActions