import React, { useState, useEffect } from 'react'
import {
  Drawer,
  List,
  Button,
  Empty,
  Typography,
  Space,
  Tag,
  Divider,
  Badge,
  Tooltip,
  Avatar,
} from 'antd'
import {
  DeleteOutlined,
  CheckOutlined,
  CloseOutlined,
  BellOutlined,
  InfoCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { useAppStore } from '@/stores'
import { formatDateTime, formatRelativeTime } from '@/utils'
import type { Notification as NotificationType } from '@/types'

const { Title, Text, Paragraph } = Typography

interface NotificationCenterProps {
  open: boolean
  onClose: () => void
  onRemoveNotification: (id: string) => void
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({
  open,
  onClose,
  onRemoveNotification,
}) => {
  const { notifications, removeNotification, clearNotifications } = useAppStore()
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all')

  // 过滤通知
  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'unread') return !notification.read
    if (filter === 'read') return notification.read
    return true
  })

  // 获取通知图标
  const getNotificationIcon = (type: NotificationType['type']) => {
    switch (type) {
      case 'success':
        return <CheckOutlined style={{ color: '#52c41a' }} />
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />
      case 'info':
      default:
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />
    }
  }

  // 获取通知颜色
  const getNotificationColor = (type: NotificationType['type']) => {
    switch (type) {
      case 'success':
        return 'success'
      case 'error':
        return 'error'
      case 'warning':
        return 'warning'
      case 'info':
      default:
        return 'default'
    }
  }

  // 标记为已读
  const markAsRead = (id: string) => {
    // 这里应该调用API更新通知状态
    // 暂时只在前端更新
    const notification = notifications.find(n => n.id === id)
    if (notification && !notification.read) {
      notification.read = true
    }
  }

  // 删除通知
  const handleRemoveNotification = (id: string) => {
    removeNotification(id)
  }

  // 清空所有通知
  const handleClearAll = () => {
    clearNotifications()
  }

  // 标记所有为已读
  const markAllAsRead = () => {
    notifications.forEach(notification => {
      if (!notification.read) {
        notification.read = true
      }
    })
  }

  // 渲染通知项
  const renderNotificationItem = (notification: NotificationType) => (
    <List.Item
      key={notification.id}
      className={`notification-item ${notification.read ? 'read' : 'unread'}`}
      actions={[
        <Tooltip title="删除">
          <Button
            type="text"
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleRemoveNotification(notification.id)}
          />
        </Tooltip>,
      ]}
      onClick={() => markAsRead(notification.id)}
    >
      <List.Item.Meta
        avatar={
          <Avatar
            icon={getNotificationIcon(notification.type)}
            style={{
              backgroundColor: notification.read ? '#f5f5f5' : undefined,
            }}
          />
        }
        title={
          <Space>
            <Text strong={!notification.read}>{notification.title}</Text>
            <Tag color={getNotificationColor(notification.type)} size="small">
              {notification.type}
            </Tag>
            {!notification.read && <Badge dot />}
          </Space>
        }
        description={
          <div>
            {notification.message && (
              <Paragraph
                ellipsis={{ rows: 2, expandable: false }}
                style={{ marginBottom: 4 }}
              >
                {notification.message}
              </Paragraph>
            )}
            <Text type="secondary" style={{ fontSize: 12 }}>
              {formatRelativeTime(notification.timestamp)}
            </Text>
          </div>
        }
      />
    </List.Item>
  )

  // 未读数量
  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <Drawer
      title={
        <div className="notification-drawer-header">
          <Space>
            <BellOutlined />
            <span>通知中心</span>
            {unreadCount > 0 && (
              <Badge count={unreadCount} size="small" />
            )}
          </Space>
        </div>
      }
      placement="right"
      width={400}
      open={open}
      onClose={onClose}
      className="notification-drawer"
      extra={
        <Space>
          {notifications.length > 0 && (
            <>
              <Tooltip title="标记全部为已读">
                <Button
                  type="text"
                  size="small"
                  icon={<CheckOutlined />}
                  onClick={markAllAsRead}
                  disabled={unreadCount === 0}
                />
              </Tooltip>
              <Tooltip title="清空所有通知">
                <Button
                  type="text"
                  size="small"
                  icon={<DeleteOutlined />}
                  onClick={handleClearAll}
                />
              </Tooltip>
            </>
          )}
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={onClose}
          />
        </Space>
      }
    >
      <div className="notification-filters">
        <Space>
          <Button
            type={filter === 'all' ? 'primary' : 'default'}
            size="small"
            onClick={() => setFilter('all')}
          >
            全部 ({notifications.length})
          </Button>
          <Button
            type={filter === 'unread' ? 'primary' : 'default'}
            size="small"
            onClick={() => setFilter('unread')}
          >
            未读 ({unreadCount})
          </Button>
          <Button
            type={filter === 'read' ? 'primary' : 'default'}
            size="small"
            onClick={() => setFilter('read')}
          >
            已读 ({notifications.length - unreadCount})
          </Button>
        </Space>
      </div>

      <Divider style={{ margin: '12px 0' }} />

      <div className="notification-list">
        {filteredNotifications.length === 0 ? (
          <Empty
            description={
              filter === 'unread'
                ? '暂无未读通知'
                : filter === 'read'
                ? '暂无已读通知'
                : '暂无通知'
            }
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            dataSource={filteredNotifications}
            renderItem={renderNotificationItem}
            size="small"
            className="notification-list-content"
          />
        )}
      </div>

      {notifications.length > 0 && (
        <div className="notification-footer">
          <Text type="secondary" style={{ fontSize: 12 }}>
            显示 {filteredNotifications.length} 条通知，共 {notifications.length} 条
          </Text>
        </div>
      )}
    </Drawer>
  )
}

export default NotificationCenter