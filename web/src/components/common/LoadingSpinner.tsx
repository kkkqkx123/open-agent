import React from 'react'
import { Spin } from 'antd'
import './LoadingSpinner.css'

interface LoadingSpinnerProps {
  size?: 'small' | 'default' | 'large'
  tip?: string
  spinning?: boolean
  children?: React.ReactNode
  className?: string
  style?: React.CSSProperties
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'default',
  tip = '加载中...',
  spinning = true,
  children,
  className = '',
  style,
}) => {
  if (children) {
    return (
      <Spin
        size={size}
        tip={tip}
        spinning={spinning}
        className={`loading-spinner-wrapper ${className}`}
        style={style}
      >
        {children}
      </Spin>
    )
  }

  return (
    <div className={`loading-spinner-container ${className}`} style={style}>
      <Spin size={size} tip={tip} spinning={spinning} />
    </div>
  )
}

export default LoadingSpinner