import React from 'react'
import { List, Avatar, Button, Tag, Space, Typography, Tooltip } from 'antd'
import {
  UserOutlined,
  ClockCircleOutlined,
  MessageOutlined,
  EyeOutlined,
  RightOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { formatRelativeTime, formatStatus } from '@/utils'
import type { Session } from '@/types'

const { Text } = Typography

interface RecentSessionsProps {
  sessions: Session[]
  onViewAll: () => void
}

const RecentSessions: React.FC<RecentSessionsProps> = ({ sessions, onViewAll }) => {
  const navigate = useNavigate()

  // 获取状态颜色
  const getStatusColor = (status: Session['status']) => {
    switch (status) {
      case 'running':
        return 'processing'
      case 'completed':
        return 'success'
      case 'failed':
        return 'error'
      case 'paused':
        return 'warning'
      default:
        return 'default'
    }
  }

  // 获取状态文本
  const getStatusText = (status: Session['status']) => {
    switch (status) {
      case 'running':
        return '运行中'
      case 'completed':
        return '已完成'
      case 'failed':
        return '失败'
      case 'paused':
        return '已暂停'
      default:
        return '未知'
    }
  }

  // 渲染会话项
  const renderSessionItem = (session: Session) => (
    <List.Item
      key={session.id}
      className="recent-session-item"
      actions={[
        <Tooltip title="查看详情">
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/history/sessions/${session.id}`)}
          />
        </Tooltip>,
      ]}
      onClick={() => navigate(`/history/sessions/${session.id}`)}
    >
      <List.Item.Meta
        avatar={
          <Avatar
            icon={<UserOutlined />}
            style={{
              backgroundColor: session.status === 'running' ? '#52c41a' : '#1890ff',
            }}
          />
        }
        title={
          <Space>
            <Text strong>{session.name}</Text>
            <Tag color={getStatusColor(session.status)} size="small">
              {getStatusText(session.status)}
            </Tag>
          </Space>
        }
        description={
          <div className="session-description">
            <div className="session-info">
              <Space size="small" split={<span>•</span>}>
                <span>
                  <MessageOutlined /> {session.messageCount} 消息
                </span>
                <span>
                  <ClockCircleOutlined /> {formatRelativeTime(session.createdAt)}
                </span>
                {session.duration && (
                  <span>
                    <ClockCircleOutlined /> {Math.round(session.duration / 1000)}s
                  </span>
                )}
              </Space>
            </div>
            {session.description && (
              <Text type="secondary" className="session-desc">
                {session.description}
              </Text>
            )}
            <div className="session-meta">
              <Space size="small">
                <Text type="secondary" style={{ fontSize: 12 }}>
                  类型: {session.agentType}
                </Text>
                {session.config && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    配置: {session.config}
                  </Text>
                )}
              </Space>
            </div>
          </div>
        }
      />
    </List.Item>
  )

  return (
    <div className="recent-sessions">
      <List
        dataSource={sessions}
        renderItem={renderSessionItem}
        size="small"
        locale={{ emptyText: '暂无会话数据' }}
      />
      
      {sessions.length > 0 && (
        <div className="view-all-container">
          <Button
            type="link"
            icon={<RightOutlined />}
            onClick={onViewAll}
            className="view-all-button"
          >
            查看全部会话
          </Button>
        </div>
      )}
    </div>
  )
}

export default RecentSessions