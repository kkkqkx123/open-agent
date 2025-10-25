import React from 'react'
import { Row, Col, Progress, Typography, Space, Button, Tag, Tooltip } from 'antd'
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type { SystemStatus } from '@/types'

const { Text, Title } = Typography

interface SystemStatusProps {
  status: SystemStatus | null | undefined
  onDetails: () => void
}

const SystemStatus: React.FC<SystemStatusProps> = ({ status, onDetails }) => {
  const navigate = useNavigate()

  // 获取状态信息
  const getStatusInfo = () => {
    if (!status) {
      return {
        color: '#d9d9d9',
        icon: <InfoCircleOutlined />,
        text: '未知',
        description: '无法获取系统状态',
      }
    }

    switch (status.status) {
      case 'healthy':
        return {
          color: '#52c41a',
          icon: <CheckCircleOutlined />,
          text: '健康',
          description: '系统运行正常',
        }
      case 'warning':
        return {
          color: '#faad14',
          icon: <ExclamationCircleOutlined />,
          text: '警告',
          description: '系统存在一些问题',
        }
      case 'error':
        return {
          color: '#ff4d4f',
          icon: <CloseCircleOutlined />,
          text: '错误',
          description: '系统出现严重问题',
        }
      default:
        return {
          color: '#d9d9d9',
          icon: <InfoCircleOutlined />,
          text: '未知',
          description: '系统状态未知',
        }
    }
  }

  // 格式化运行时间
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (days > 0) {
      return `${days}天 ${hours}小时`
    } else if (hours > 0) {
      return `${hours}小时 ${minutes}分钟`
    } else {
      return `${minutes}分钟`
    }
  }

  // 计算健康分数
  const getHealthScore = () => {
    if (!status) return 0

    switch (status.status) {
      case 'healthy':
        return 100
      case 'warning':
        return 70
      case 'error':
        return 30
      default:
        return 50
    }
  }

  const statusInfo = getStatusInfo()
  const healthScore = getHealthScore()

  return (
    <div className="system-status">
      {/* 状态概览 */}
      <div className="status-overview">
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <div className="status-header">
            <Space>
              <span style={{ color: statusInfo.color, fontSize: 24 }}>
                {statusInfo.icon}
              </span>
              <div>
                <Title level={5} style={{ margin: 0, color: statusInfo.color }}>
                  {statusInfo.text}
                </Title>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {statusInfo.description}
                </Text>
              </div>
            </Space>
          </div>

          {/* 健康分数 */}
          <div className="health-score">
            <div className="score-label">
              <Text type="secondary">健康分数</Text>
            </div>
            <Progress
              percent={healthScore}
              strokeColor={statusInfo.color}
              trailColor="#f0f0f0"
              strokeWidth={8}
              format={(percent) => `${percent}%`}
            />
          </div>
        </Space>
      </div>

      {/* 系统指标 */}
      {status && (
        <div className="system-metrics">
          <Row gutter={[8, 8]}>
            <Col span={12}>
              <div className="metric-item">
                <Text type="secondary" style={{ fontSize: 12 }}>
                  运行时间
                </Text>
                <div className="metric-value">
                  <Text strong>{formatUptime(status.uptime)}</Text>
                </div>
              </div>
            </Col>
            <Col span={12}>
              <div className="metric-item">
                <Text type="secondary" style={{ fontSize: 12 }}>
                  版本
                </Text>
                <div className="metric-value">
                  <Text strong>{status.version}</Text>
                </div>
              </div>
            </Col>
            <Col span={12}>
              <div className="metric-item">
                <Text type="secondary" style={{ fontSize: 12 }}>
                  环境
                </Text>
                <div className="metric-value">
                  <Tag
                    color={status.environment === 'production' ? 'red' : 'blue'}
                    size="small"
                  >
                    {status.environment}
                  </Tag>
                </div>
              </div>
            </Col>
            <Col span={12}>
              <div className="metric-item">
                <Text type="secondary" style={{ fontSize: 12 }}>
                  最后检查
                </Text>
                <div className="metric-value">
                  <Text strong>
                    {new Date(status.lastCheck).toLocaleTimeString()}
                  </Text>
                </div>
              </div>
            </Col>
          </Row>
        </div>
      )}

      {/* 操作按钮 */}
      <div className="status-actions">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button
            type="primary"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => navigate('/config')}
            block
          >
            系统配置
          </Button>
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => window.location.reload()}
            block
          >
            刷新状态
          </Button>
          <Button
            type="link"
            size="small"
            onClick={onDetails}
            block
          >
            查看详情
          </Button>
        </Space>
      </div>
    </div>
  )
}

export default SystemStatus