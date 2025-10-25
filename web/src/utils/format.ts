import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/duration'

dayjs.locale('zh-cn')
dayjs.extend(relativeTime)
dayjs.extend(duration)

// 格式化日期时间
export const formatDateTime = (
  date: string | Date | number,
  format = 'YYYY-MM-DD HH:mm:ss'
): string => {
  return dayjs(date).format(format)
}

// 格式化相对时间
export const formatRelativeTime = (date: string | Date | number): string => {
  return dayjs(date).fromNow()
}

// 格式化持续时间
export const formatDuration = (milliseconds: number): string => {
  const duration = dayjs.duration(milliseconds)
  
  if (duration.asDays() >= 1) {
    return `${Math.floor(duration.asDays())}天 ${duration.hours()}小时`
  } else if (duration.asHours() >= 1) {
    return `${Math.floor(duration.asHours())}小时 ${duration.minutes()}分钟`
  } else if (duration.asMinutes() >= 1) {
    return `${Math.floor(duration.asMinutes())}分钟 ${duration.seconds()}秒`
  } else {
    return `${duration.seconds()}秒`
  }
}

// 格式化文件大小
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

// 格式化数字
export const formatNumber = (
  num: number,
  options?: {
    decimals?: number
    separator?: string
    prefix?: string
    suffix?: string
  }
): string => {
  const {
    decimals = 2,
    separator = ',',
    prefix = '',
    suffix = ''
  } = options || {}

  const formatted = num.toFixed(decimals)
  const parts = formatted.split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, separator)
  
  return `${prefix}${parts.join('.')}${suffix}`
}

// 格式化百分比
export const formatPercentage = (
  value: number,
  decimals = 1,
  multiplyBy100 = true
): string => {
  const percentage = multiplyBy100 ? value * 100 : value
  return `${percentage.toFixed(decimals)}%`
}

// 格式化货币
export const formatCurrency = (
  amount: number,
  currency = '¥',
  decimals = 2
): string => {
  return formatNumber(amount, {
    decimals,
    prefix: currency,
    separator: ','
  })
}

// 格式化响应时间
export const formatResponseTime = (milliseconds: number): string => {
  if (milliseconds < 1000) {
    return `${Math.round(milliseconds)}ms`
  } else if (milliseconds < 60000) {
    return `${(milliseconds / 1000).toFixed(1)}s`
  } else {
    return `${(milliseconds / 60000).toFixed(1)}min`
  }
}

// 格式化速率
export const formatRate = (
  value: number,
  unit: string,
  perUnit: string = '秒'
): string => {
  return `${formatNumber(value)} ${unit}/${perUnit}`
}

// 格式化状态
export const formatStatus = (status: string): { text: string; color: string } => {
  const statusMap: Record<string, { text: string; color: string }> = {
    running: { text: '运行中', color: '#52c41a' },
    completed: { text: '已完成', color: '#52c41a' },
    failed: { text: '失败', color: '#ff4d4f' },
    paused: { text: '已暂停', color: '#faad14' },
    pending: { text: '等待中', color: '#1890ff' },
    idle: { text: '空闲', color: '#8c8c8c' },
    active: { text: '活跃', color: '#52c41a' },
    inactive: { text: '非活跃', color: '#8c8c8c' },
    online: { text: '在线', color: '#52c41a' },
    offline: { text: '离线', color: '#ff4d4f' },
    healthy: { text: '健康', color: '#52c41a' },
    warning: { text: '警告', color: '#faad14' },
    error: { text: '错误', color: '#ff4d4f' },
    critical: { text: '严重', color: '#ff4d4f' },
  }

  return statusMap[status.toLowerCase()] || {
    text: status,
    color: '#8c8c8c'
  }
}

// 格式化错误类型
export const formatErrorType = (type: string): { text: string; color: string } => {
  const errorTypeMap: Record<string, { text: string; color: string }> = {
    system: { text: '系统错误', color: '#ff4d4f' },
    network: { text: '网络错误', color: '#faad14' },
    validation: { text: '验证错误', color: '#1890ff' },
    business: { text: '业务错误', color: '#722ed1' },
    timeout: { text: '超时错误', color: '#faad14' },
    permission: { text: '权限错误', color: '#ff4d4f' },
    not_found: { text: '未找到', color: '#8c8c8c' },
  }

  return errorTypeMap[type.toLowerCase()] || {
    text: type,
    color: '#8c8c8c'
  }
}

// 格式化标签
export const formatTags = (tags: string[]): string[] => {
  return tags.map(tag => {
    // 移除特殊字符，转换为小写
    return tag.replace(/[^\w\u4e00-\u9fa5]/g, '').toLowerCase()
  }).filter(tag => tag.length > 0)
}

// 格式化URL
export const formatUrl = (url: string): string => {
  if (!url) return ''
  
  // 如果没有协议，添加https://
  if (!/^https?:\/\//i.test(url)) {
    return `https://${url}`
  }
  
  return url
}

// 格式化邮箱
export const formatEmail = (email: string): string => {
  return email.toLowerCase().trim()
}

// 格式化手机号
export const formatPhone = (phone: string): string => {
  // 移除所有非数字字符
  const cleaned = phone.replace(/\D/g, '')
  
  // 中国手机号格式
  if (cleaned.length === 11) {
    return `${cleaned.slice(0, 3)} ${cleaned.slice(3, 7)} ${cleaned.slice(7)}`
  }
  
  return phone
}

// 格式化ID（隐藏中间部分）
export const formatId = (id: string, visibleChars = 4): string => {
  if (id.length <= visibleChars * 2) {
    return id
  }
  
  const start = id.slice(0, visibleChars)
  const end = id.slice(-visibleChars)
  const middle = '*'.repeat(Math.max(3, id.length - visibleChars * 2))
  
  return `${start}${middle}${end}`
}

// 格式化JSON
export const formatJson = (obj: any, indent = 2): string => {
  try {
    return JSON.stringify(obj, null, indent)
  } catch (error) {
    return String(obj)
  }
}

// 格式化SQL
export const formatSql = (sql: string): string => {
  // 简单的SQL格式化
  return sql
    .replace(/\s+/g, ' ')
    .replace(/,/g, ',\n  ')
    .replace(/\bFROM\b/gi, '\nFROM')
    .replace(/\bWHERE\b/gi, '\nWHERE')
    .replace(/\bORDER BY\b/gi, '\nORDER BY')
    .replace(/\bGROUP BY\b/gi, '\nGROUP BY')
    .replace(/\bHAVING\b/gi, '\nHAVING')
    .trim()
}

// 格式化版本号
export const formatVersion = (version: string): string => {
  // 确保版本号格式为 x.y.z
  const parts = version.split('.').map(part => parseInt(part, 10))
  
  while (parts.length < 3) {
    parts.push(0)
  }
  
  return parts.slice(0, 3).join('.')
}

// 格式化哈希值
export const formatHash = (hash: string, length = 8): string => {
  return hash.slice(0, length)
}

// 格式化UUID
export const formatUuid = (uuid: string): string => {
  // 确保UUID格式正确
  const cleaned = uuid.replace(/[^\w-]/g, '')
  
  if (cleaned.length === 32) {
    // 添加连字符
    return [
      cleaned.slice(0, 8),
      cleaned.slice(8, 12),
      cleaned.slice(12, 16),
      cleaned.slice(16, 20),
      cleaned.slice(20)
    ].join('-')
  }
  
  return cleaned
}

export default {
  formatDateTime,
  formatRelativeTime,
  formatDuration,
  formatFileSize,
  formatNumber,
  formatPercentage,
  formatCurrency,
  formatResponseTime,
  formatRate,
  formatStatus,
  formatErrorType,
  formatTags,
  formatUrl,
  formatEmail,
  formatPhone,
  formatId,
  formatJson,
  formatSql,
  formatVersion,
  formatHash,
  formatUuid,
}