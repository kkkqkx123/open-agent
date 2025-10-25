// 验证工具函数

// 验证邮箱
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// 验证手机号（中国）
export const isValidPhone = (phone: string): boolean => {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phone.replace(/\D/g, ''))
}

// 验证URL
export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

// 验证IP地址
export const isValidIp = (ip: string): boolean => {
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  return ipRegex.test(ip)
}

// 验证端口号
export const isValidPort = (port: number): boolean => {
  return Number.isInteger(port) && port >= 1 && port <= 65535
}

// 验证JSON
export const isValidJson = (str: string): boolean => {
  try {
    JSON.parse(str)
    return true
  } catch {
    return false
  }
}

// 验证UUID
export const isValidUuid = (uuid: string): boolean => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  return uuidRegex.test(uuid)
}

// 验证日期
export const isValidDate = (date: string | Date): boolean => {
  const d = new Date(date)
  return d instanceof Date && !isNaN(d.getTime())
}

// 验证数字
export const isNumber = (value: any): value is number => {
  return typeof value === 'number' && !isNaN(value)
}

// 验证整数
export const isInteger = (value: any): value is number => {
  return Number.isInteger(value)
}

// 验证正数
export const isPositive = (value: number): boolean => {
  return value > 0
}

// 验证非负数
export const isNonNegative = (value: number): boolean => {
  return value >= 0
}

// 验证字符串长度
export const isValidLength = (
  str: string,
  options: {
    min?: number
    max?: number
    exact?: number
  }
): boolean => {
  const { min, max, exact } = options
  
  if (exact !== undefined) {
    return str.length === exact
  }
  
  if (min !== undefined && str.length < min) {
    return false
  }
  
  if (max !== undefined && str.length > max) {
    return false
  }
  
  return true
}

// 验证密码强度
export const isValidPassword = (password: string): {
  isValid: boolean
  strength: 'weak' | 'medium' | 'strong'
  errors: string[]
} => {
  const errors: string[] = []
  let score = 0

  // 长度检查
  if (password.length < 8) {
    errors.push('密码长度至少8位')
  } else {
    score += 1
  }

  // 包含小写字母
  if (/[a-z]/.test(password)) {
    score += 1
  } else {
    errors.push('密码必须包含小写字母')
  }

  // 包含大写字母
  if (/[A-Z]/.test(password)) {
    score += 1
  } else {
    errors.push('密码必须包含大写字母')
  }

  // 包含数字
  if (/\d/.test(password)) {
    score += 1
  } else {
    errors.push('密码必须包含数字')
  }

  // 包含特殊字符
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    score += 1
  } else {
    errors.push('密码必须包含特殊字符')
  }

  let strength: 'weak' | 'medium' | 'strong' = 'weak'
  if (score >= 4) {
    strength = 'strong'
  } else if (score >= 2) {
    strength = 'medium'
  }

  return {
    isValid: errors.length === 0,
    strength,
    errors
  }
}

// 验证用户名
export const isValidUsername = (username: string): boolean => {
  // 用户名规则：4-20位，只能包含字母、数字、下划线、连字符
  const usernameRegex = /^[a-zA-Z0-9_-]{4,20}$/
  return usernameRegex.test(username)
}

// 验证文件名
export const isValidFileName = (fileName: string): boolean => {
  // 不能包含的字符
  const invalidChars = /[<>:"/\\|?*]/
  if (invalidChars.test(fileName)) {
    return false
  }

  // 不能为空或只包含空格
  if (!fileName.trim()) {
    return false
  }

  // 不能是保留名称（Windows）
  const reservedNames = [
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
  ]

  const nameWithoutExt = fileName.split('.')[0].toUpperCase()
  if (reservedNames.includes(nameWithoutExt)) {
    return false
  }

  return true
}

// 验证文件扩展名
export const isValidFileExtension = (
  fileName: string,
  allowedExtensions: string[]
): boolean => {
  const extension = fileName.split('.').pop()?.toLowerCase()
  if (!extension) {
    return false
  }

  return allowedExtensions.some(ext => ext.toLowerCase() === extension)
}

// 验证颜色值
export const isValidColor = (color: string): boolean => {
  // 十六进制颜色
  const hexRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/
  if (hexRegex.test(color)) {
    return true
  }

  // RGB颜色
  const rgbRegex = /^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$/
  if (rgbRegex.test(color)) {
    return true
  }

  // RGBA颜色
  const rgbaRegex = /^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(0|1|0?\.\d+)\s*\)$/
  if (rgbaRegex.test(color)) {
    return true
  }

  // 颜色名称
  const colorNames = [
    'red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink', 'brown',
    'black', 'white', 'gray', 'grey', 'cyan', 'magenta', 'lime', 'navy',
    'teal', 'olive', 'maroon', 'aqua', 'fuchsia', 'silver', 'gold'
  ]

  return colorNames.includes(color.toLowerCase())
}

// 验证正则表达式
export const isValidRegex = (pattern: string): boolean => {
  try {
    new RegExp(pattern)
    return true
  } catch {
    return false
  }
}

// 验证版本号
export const isValidVersion = (version: string): boolean => {
  const versionRegex = /^\d+(\.\d+)*$/
  return versionRegex.test(version)
}

// 验证语义化版本号
export const isValidSemanticVersion = (version: string): boolean => {
  const semverRegex = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/
  return semverRegex.test(version)
}

// 验证域名
export const isValidDomain = (domain: string): boolean => {
  const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9])*$/
  return domainRegex.test(domain)
}

// 验证MAC地址
export const isValidMacAddress = (mac: string): boolean => {
  const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/
  return macRegex.test(mac)
}

// 验证ISBN
export const isValidIsbn = (isbn: string): boolean => {
  // 移除连字符和空格
  const cleanIsbn = isbn.replace(/[-\s]/g, '')
  
  // ISBN-10
  if (cleanIsbn.length === 10) {
    const isbn10Regex = /^\d{9}[\dX]$/
    if (!isbn10Regex.test(cleanIsbn)) {
      return false
    }

    let sum = 0
    for (let i = 0; i < 9; i++) {
      sum += (10 - i) * parseInt(cleanIsbn[i])
    }
    sum += cleanIsbn[9] === 'X' ? 10 : parseInt(cleanIsbn[9])

    return sum % 11 === 0
  }

  // ISBN-13
  if (cleanIsbn.length === 13) {
    const isbn13Regex = /^\d{13}$/
    if (!isbn13Regex.test(cleanIsbn)) {
      return false
    }

    let sum = 0
    for (let i = 0; i < 12; i++) {
      sum += parseInt(cleanIsbn[i]) * (i % 2 === 0 ? 1 : 3)
    }
    const checkDigit = (10 - (sum % 10)) % 10

    return checkDigit === parseInt(cleanIsbn[12])
  }

  return false
}

// 验证身份证号（中国）
export const isValidChineseId = (id: string): boolean => {
  // 18位身份证号
  const id18Regex = /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/
  if (!id18Regex.test(id)) {
    return false
  }

  // 验证校验码
  const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  const checkCodes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

  let sum = 0
  for (let i = 0; i < 17; i++) {
    sum += parseInt(id[i]) * weights[i]
  }

  const checkCode = checkCodes[sum % 11]
  return checkCode === id[17].toUpperCase()
}

// 验证银行卡号
export const isValidBankCard = (cardNumber: string): boolean => {
  // 移除所有非数字字符
  const cleaned = cardNumber.replace(/\D/g, '')
  
  // 银行卡号长度通常为13-19位
  if (cleaned.length < 13 || cleaned.length > 19) {
    return false
  }

  // Luhn算法验证
  let sum = 0
  let isEven = false

  for (let i = cleaned.length - 1; i >= 0; i--) {
    let digit = parseInt(cleaned[i])

    if (isEven) {
      digit *= 2
      if (digit > 9) {
        digit -= 9
      }
    }

    sum += digit
    isEven = !isEven
  }

  return sum % 10 === 0
}

// 验证数组
export const isArray = (value: any): value is any[] => {
  return Array.isArray(value)
}

// 验证对象
export const isObject = (value: any): value is Record<string, any> => {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

// 验证空值
export const isEmpty = (value: any): boolean => {
  if (value === null || value === undefined) {
    return true
  }

  if (typeof value === 'string') {
    return value.trim().length === 0
  }

  if (Array.isArray(value)) {
    return value.length === 0
  }

  if (typeof value === 'object') {
    return Object.keys(value).length === 0
  }

  return false
}

// 验证函数
export const isFunction = (value: any): value is Function => {
  return typeof value === 'function'
}

// 验证Promise
export const isPromise = (value: any): value is Promise<any> => {
  return value instanceof Promise || (
    value !== null &&
    typeof value === 'object' &&
    typeof value.then === 'function' &&
    typeof value.catch === 'function'
  )
}

export default {
  isValidEmail,
  isValidPhone,
  isValidUrl,
  isValidIp,
  isValidPort,
  isValidJson,
  isValidUuid,
  isValidDate,
  isNumber,
  isInteger,
  isPositive,
  isNonNegative,
  isValidLength,
  isValidPassword,
  isValidUsername,
  isValidFileName,
  isValidFileExtension,
  isValidColor,
  isValidRegex,
  isValidVersion,
  isValidSemanticVersion,
  isValidDomain,
  isValidMacAddress,
  isValidIsbn,
  isValidChineseId,
  isValidBankCard,
  isArray,
  isObject,
  isEmpty,
  isFunction,
  isPromise,
}