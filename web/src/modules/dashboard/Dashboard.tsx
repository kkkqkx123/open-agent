import React, { useEffect } from 'react'
import { Row, Col, Card, Statistic, Progress, Space, Button, Typography } from 'antd'
import {
  DashboardOutlined,
  NodeIndexOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  TrendingUpOutlined,
  WarningOutlined,
  RocketOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAppStore } from '@/stores'
import { sessionService, workflowService, analyticsService } from '@/services'
import MetricsChart from '@/components/charts/MetricsChart'
import RecentSessions from './RecentSessions'
import SystemStatus from './SystemStatus'
import QuickActions from './QuickActions'
import ActivityFeed from './ActivityFeed'
import AppContent from '@/components/layout/AppContent'

const { Title, Text } = Typography

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { setActiveModule, loadMetrics } = useAppStore()

  // 获取会话数据
  const { data: sessions = [], isLoading: sessionsLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => sessionService.listSessions(),
    refetchInterval: 30000, // 30秒刷新一次
  })

  // 获取工作流数据
  const { data: workflows = [], isLoading: workflowsLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowService.listWorkflows(),
    refetchInterval: 30000,
  })

  // 获取实时指标
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: () => analyticsService.getRealTimeMetrics(),
    refetchInterval: 5000, // 5秒刷新一次
  })

  // 获取系统状态
  const { data: systemStatus } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: () => analyticsService.getSystemStatus(),
    refetchInterval: 10000, // 10秒刷新一次
  })

  // 计算统计数据
  const stats = {
    totalSessions: sessions.items?.length || 0,
    activeSessions: sessions.items?.filter(s => s.status === 'running').length || 0,
    totalWorkflows: workflows.items?.length || 0,
    activeWorkflows: workflows.items?.filter(w => w.status === 'active').length || 0,
    avgResponseTime: metrics?.responseTime || 0,
    successRate: metrics ? 100 - (metrics.errorRate * 100) : 0,
    totalCost: metrics ? metrics.totalCost / 100 : 0, // 转换为元
    throughput: metrics?.throughput || 0,
  }

  // 设置当前模块
  useEffect(() => {
    setActiveModule('dashboard')
  }, [setActiveModule])

  // 刷新数据
  const handleRefresh = () => {
    loadMetrics()
    window.location.reload()
  }

  return (
    <AppContent
      title="仪表板"
      subtitle="系统概览和实时监控"
      extra={
        <Button
          type="primary"
          icon={<ReloadOutlined />}
          onClick={handleRefresh}
          loading={sessionsLoading || workflowsLoading || metricsLoading}
        >
          刷新数据
        </Button>
      }
    >
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总会话数"
              value={stats.totalSessions}
              prefix={<DashboardOutlined />}
              valueStyle={{ color: '#1890ff' }}
              loading={sessionsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃会话"
              value={stats.activeSessions}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#52c41a' }}
              loading={sessionsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={stats.avgResponseTime}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
              loading={metricsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="成功率"
              value={stats.successRate}
              precision={1}
              suffix="%"
              prefix={
                <Progress
                  percent={stats.successRate}
                  size="small"
                  style={{ width: 60 }}
                  showInfo={false}
                />
              }
              valueStyle={{ color: '#52c41a' }}
              loading={metricsLoading}
            />
          </Card>
        </Col>
      </Row>

      {/* 第二行统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="工作流总数"
              value={stats.totalWorkflows}
              prefix={<NodeIndexOutlined />}
              valueStyle={{ color: '#722ed1' }}
              loading={workflowsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃工作流"
              value={stats.activeWorkflows}
              prefix={<TrendingUpOutlined />}
              valueStyle={{ color: '#52c41a' }}
              loading={workflowsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="吞吐量"
              value={stats.throughput}
              suffix="/min"
              prefix={<TrendingUpOutlined />}
              valueStyle={{ color: '#1890ff' }}
              loading={metricsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总成本"
              value={stats.totalCost}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: '#faad14' }}
              loading={metricsLoading}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表和详细信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="性能趋势" loading={metricsLoading}>
            <MetricsChart
              data={[]}
              height={300}
              type="performance"
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="成本分析" loading={metricsLoading}>
            <MetricsChart
              data={[]}
              height={300}
              type="cost"
            />
          </Card>
        </Col>
      </Row>

      {/* 最近活动和系统状态 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card title="最近会话" loading={sessionsLoading}>
            <RecentSessions
              sessions={sessions.items?.slice(0, 5) || []}
              onViewAll={() => navigate('/history')}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="系统状态" loading={!systemStatus}>
            <SystemStatus
              status={systemStatus}
              onDetails={() => navigate('/analytics')}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="活动动态" loading={metricsLoading}>
            <ActivityFeed
              activities={[]}
              onViewAll={() => navigate('/history')}
            />
          </Card>
        </Col>
      </Row>

      {/* 快速操作 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title="快速操作">
            <QuickActions />
          </Card>
        </Col>
      </Row>
    </AppContent>
  )
}

export default Dashboard