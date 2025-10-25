import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'
import { ApiResponse } from '@/types'

export class BaseService {
  protected api: AxiosInstance

  constructor(baseURL: string) {
    this.api = axios.create({
      baseURL,
      timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // 请求拦截器
    this.api.interceptors.request.use(
      (config) => {
        // 添加认证token
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // 添加请求ID用于追踪
        config.headers['X-Request-ID'] = this.generateRequestId()

        // 记录请求开始时间
        config.metadata = { startTime: new Date() }

        return config
      },
      (error) => {
        console.error('请求拦截器错误:', error)
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.api.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        // 计算请求耗时
        const endTime = new Date()
        const startTime = response.config.metadata?.startTime
        if (startTime) {
          const duration = endTime.getTime() - startTime.getTime()
          console.log(`API请求耗时: ${duration}ms - ${response.config.url}`)
        }

        // 统一处理响应格式
        const { data } = response
        if (data.success === false) {
          message.error(data.message || '请求失败')
          return Promise.reject(new Error(data.message || '请求失败'))
        }

        return data
      },
      (error) => {
        // 统一错误处理
        this.handleError(error)
        return Promise.reject(error)
      }
    )
  }

  private handleError(error: any) {
    let errorMessage = '请求失败，请稍后重试'

    if (error.response) {
      // 服务器响应错误
      const { status, data } = error.response

      switch (status) {
        case 400:
          errorMessage = data.message || '请求参数错误'
          break
        case 401:
          errorMessage = '未授权，请重新登录'
          // 清除token并跳转到登录页
          localStorage.removeItem('token')
          window.location.href = '/login'
          break
        case 403:
          errorMessage = '权限不足'
          break
        case 404:
          errorMessage = '请求的资源不存在'
          break
        case 422:
          errorMessage = data.message || '数据验证失败'
          break
        case 500:
          errorMessage = '服务器内部错误'
          break
        case 502:
          errorMessage = '网关错误'
          break
        case 503:
          errorMessage = '服务不可用'
          break
        default:
          errorMessage = data.message || `请求失败 (${status})`
      }
    } else if (error.request) {
      // 网络错误
      if (error.code === 'ECONNABORTED') {
        errorMessage = '请求超时，请检查网络连接'
      } else {
        errorMessage = '网络连接失败，请检查网络设置'
      }
    } else {
      // 其他错误
      errorMessage = error.message || '未知错误'
    }

    // 显示错误消息
    message.error(errorMessage)

    // 记录错误日志
    console.error('API错误:', {
      message: errorMessage,
      error,
      timestamp: new Date().toISOString(),
    })
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // 通用GET请求
  protected async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.api.get(url, config)
  }

  // 通用POST请求
  protected async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.api.post(url, data, config)
  }

  // 通用PUT请求
  protected async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.api.put(url, data, config)
  }

  // 通用PATCH请求
  protected async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.api.patch(url, data, config)
  }

  // 通用DELETE请求
  protected async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.api.delete(url, config)
  }

  // 文件上传
  protected async upload<T = any>(url: string, file: File, config?: AxiosRequestConfig): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)

    return this.api.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers,
      },
    })
  }

  // 文件下载
  protected async download(url: string, filename?: string, config?: AxiosRequestConfig): Promise<void> {
    const response = await this.api.get(url, {
      ...config,
      responseType: 'blob',
    })

    // 创建下载链接
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }

  // 取消请求
  protected createCancelToken() {
    return axios.CancelToken.source()
  }

  // 检查请求是否被取消
  protected isCancel(error: any): boolean {
    return axios.isCancel(error)
  }
}

// 扩展AxiosRequestConfig以支持metadata
declare module 'axios' {
  interface AxiosRequestConfig {
    metadata?: {
      startTime?: Date
    }
  }
}

export default BaseService