import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Result, Button } from 'antd'
import { ReloadOutlined, HomeOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    })

    // 调用自定义错误处理函数
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // 记录错误到控制台
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    // 在生产环境中，可以将错误发送到错误监控服务
    if (process.env.NODE_ENV === 'production') {
      // 这里可以集成Sentry、LogRocket等错误监控服务
      // Sentry.captureException(error, { contexts: { react: { componentStack: errorInfo.componentStack } } })
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback
      }

      // 默认错误UI
      return (
        <ErrorBoundaryUI
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onRetry={this.handleRetry}
          onGoHome={this.handleGoHome}
        />
      )
    }

    return this.props.children
  }
}

// 错误边界UI组件
interface ErrorBoundaryUIProps {
  error: Error | null
  errorInfo: ErrorInfo | null
  onRetry: () => void
  onGoHome: () => void
}

const ErrorBoundaryUI: React.FC<ErrorBoundaryUIProps> = ({
  error,
  errorInfo,
  onRetry,
  onGoHome,
}) => {
  const navigate = useNavigate()

  const handleReportError = () => {
    // 在实际应用中，这里可以发送错误报告
    const errorReport = {
      message: error?.message,
      stack: error?.stack,
      componentStack: errorInfo?.componentStack,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    }

    console.log('Error Report:', errorReport)
    
    // 可以复制错误信息到剪贴板
    navigator.clipboard.writeText(JSON.stringify(errorReport, null, 2))
      .then(() => {
        alert('错误信息已复制到剪贴板')
      })
      .catch(() => {
        alert('复制失败，请手动复制错误信息')
      })
  }

  return (
    <div className="error-boundary-container">
      <Result
        status="error"
        title="页面出现错误"
        subTitle="抱歉，页面遇到了一些问题。您可以尝试刷新页面或返回首页。"
        extra={[
          <Button
            type="primary"
            key="retry"
            icon={<ReloadOutlined />}
            onClick={onRetry}
          >
            重试
          </Button>,
          <Button
            key="home"
            icon={<HomeOutlined />}
            onClick={() => navigate('/')}
          >
            返回首页
          </Button>,
          <Button
            key="report"
            onClick={handleReportError}
          >
            报告错误
          </Button>,
        ]}
      >
        {process.env.NODE_ENV === 'development' && error && (
          <div className="error-details">
            <h4>错误详情（仅开发环境显示）</h4>
            <details style={{ whiteSpace: 'pre-wrap' }}>
              <summary>错误堆栈</summary>
              {error.stack}
            </details>
            {errorInfo && (
              <details style={{ whiteSpace: 'pre-wrap', marginTop: 16 }}>
                <summary>组件堆栈</summary>
                {errorInfo.componentStack}
              </details>
            )}
          </div>
        )}
      </Result>
    </div>
  )
}

export default ErrorBoundary