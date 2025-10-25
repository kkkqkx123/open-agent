import React from 'react'
import { List, Avatar, Button, Space, Typography, Tag, Tooltip } from 'antd'
import {
  UserOutlined,
  RobotOutlined,
  BranchesOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  MessageOutlined,
  ToolOutlined,
  RightOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { formatRelativeTime } from '@/utils'

const { Text } = Typography

interface Activity {
  id: string
  type: 'session' | 'workflow' | 'system' | 'error'
  title: string
  description: string
  timestamp: number
  user?: string
  status?: 'success' | 'warning' | 'error' | 'info'
  metadata?: Record<string, any>
}

interface ActivityFeedProps {
  activities: Activity[]
  onViewAll: () => void
}

const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities, onViewAll }) => {
  const navigate = useNavigate()

  // 模拟活动数据
  const mockActivities: Activity[] = [
    {
      id: '1',
      type: 'session',
      title: '新会话创建',
      description: '用户创建了新的对话会话',
      timestamp: Date.now() - 5 * 60 * 1000,
      user: '张三',
      status: 'success',
      metadata: { sessionId: 'session-123' },
    },
    {
      id: '2',
      type: 'workflow',
      title: '工作流执行完成',
      description: '数据处理工作流成功执行',
      timestamp: Date.now() - 15 * 60 * 1000,
      user: '系统',
      status: 'success',
      metadata: { workflowId: 'workflow-456' },
    },
    {
      id: '3',
      type: 'error',
      title: 'API调用失败',
      description: '外部API调用超时',
      timestamp: Date.now() - 30 * 60 * 1000,
      user: '系统',
      status: 'error',
      metadata: { errorId: 'error-789' },
    },
    {
      id: '4',
      type: 'system',
      title: '系统备份完成',
      description: '自动备份任务成功完成',
      timestamp: Date.now() - 60 * 60 * 1000,
      user: '系统',
      status: 'info',
      metadata: { backupId: 'backup-010' },
    },
    {
      id: '5',
      type: 'workflow',
      title: '工作流执行失败',
      description: '数据分析工作流执行失败',
      timestamp: Date.now() - 2 * 60 * 60 * 1000,
      user: '李四',
      status: 'error',
      metadata: { workflowId: 'workflow-011' },
    },
  ]

  const displayActivities = activities.length > 0 ? activities : mockActivities

  // 获取活动图标
  const getActivityIcon = (type: Activity['type'], status?: Activity['status']) => {
    switch (type) {
      case 'session':
        return <UserOutlined />
      case 'workflow':
        return <BranchesOutlined />
      case 'system':
        return <RobotOutlined />
      case 'error':
        return <ExclamationCircleOutlined />
      default:
        return <MessageOutlined />
    }
  }

  // 获取状态颜色
  const getStatusColor = (status?: Activity['status']) => {
    switch (status) {
      case 'success':
        return 'success'
      case 'warning':
        return 'warning'
      case 'error':
        return 'error'
      case 'info':
      default:
        return 'default'
    }
  }

  // 获取活动类型颜色
  const getActivityColor = (type: Activity['type']) => {
    switch (type) {
      case 'session':
        return '#1890ff'
      case 'workflow':
        return '#52c41a'
      case 'system':
        return '#722ed1'
      case 'error':
        return '#ff4d4f'
      default:
        return '#8c8c8c'
    }
  }

  // 处理活动点击
  const handleActivityClick = (activity: Activity) => {
    switch (activity.type) {
      case 'session':
        if (activity.metadata?.sessionId) {
          navigate(`/history/sessions/${activity.metadata.sessionId}`)
        }
        break
      case 'workflow':
        if (activity.metadata?.workflowId) {
          navigate(`/workflows/${activity.metadata.workflowId}`)
        }
        break
      case 'error':
        if (activity.metadata?.errorId) {
          navigate(`/errors/${activity.metadata.errorId}`)
        }
        break
      default:
        break
    }
  }

  // 渲染活动项
  const renderActivityItem = (activity: Activity) => (
    <List.Item
      key={activity.id}
      className="activity-item"
      actions={[
        <Tooltip title="查看详情">
          <Button
            type="text"
            size="small"
            icon={<RightOutlined />}
            onClick={() => handleActivityClick(activity)}
          />
        </Tooltip>,
      ]}
      onClick={() => handleActivityClick(activity)}
    >
      <List.Item.Meta
        avatar={
          <Avatar
            icon={getActivityIcon(activity.type, activity.status)}
            style={{
              backgroundColor: getActivityColor(activity.type),
            }}
          />
        }
        title={
          <Space>
            <Text strong>{activity.title}</Text>
            {activity.status && (
              <Tag color={getStatusColor(activity.status)} size="small">
                {activity.status}
              </Tag>
            )}
          </Space>
        }
        description={
          <div className="activity-description">
            <div className="activity-info">
              <Space size="small" split={<span>•</span>}>
                <span>{activity.description}</span>
                {activity.user && (
                  <span>
                    <UserOutlined /> {activity.user}
                  </span>
                )}
                <span>
                  <ClockCircleOutlined /> {formatRelativeTime(activity.timestamp)}
                </span>
              </Space>
            </div>
          </div>
        }
      />
    </List.Item>
  )

  return (
    <div className="activity-feed">
      <List
        dataSource={displayActivities.slice(0, 5)}
        renderItem={renderActivityItem}
        size="small"
        locale={{ emptyText: '暂无活动记录' }}
      />
      
      {displayActivities.length > 0 && (
        <div className="view-all-container">
          <Button
            type="link"
            icon={<RightOutlined />}
            onClick={onViewAll}
            className="view-all-button"
          >
            查看全部动态
          </Button>
        </div>
      )}
    </div>
  )
}

export default ActivityFeed