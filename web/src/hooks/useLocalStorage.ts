import { useState, useEffect, useCallback } from 'react'
import { storageService } from '@/services'

// 本地存储Hook
export const useLocalStorage = <T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = storageService.getItem(key)
      return item !== null ? item : initialValue
    } catch (error) {
      console.error(`获取本地存储 ${key} 失败:`, error)
      return initialValue
    }
  })

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value
        setStoredValue(valueToStore)
        storageService.setItem(key, valueToStore)
      } catch (error) {
        console.error(`设置本地存储 ${key} 失败:`, error)
      }
    },
    [key, storedValue]
  )

  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue)
      storageService.removeItem(key)
    } catch (error) {
      console.error(`删除本地存储 ${key} 失败:`, error)
    }
  }, [key, initialValue])

  return [storedValue, setValue, removeValue]
}

// 会话存储Hook
export const useSessionStorage = <T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = sessionStorage.getItem(key)
      return item !== null ? JSON.parse(item) : initialValue
    } catch (error) {
      console.error(`获取会话存储 ${key} 失败:`, error)
      return initialValue
    }
  })

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value
        setStoredValue(valueToStore)
        sessionStorage.setItem(key, JSON.stringify(valueToStore))
      } catch (error) {
        console.error(`设置会话存储 ${key} 失败:`, error)
      }
    },
    [key, storedValue]
  )

  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue)
      sessionStorage.removeItem(key)
    } catch (error) {
      console.error(`删除会话存储 ${key} 失败:`, error)
    }
  }, [key, initialValue])

  return [storedValue, setValue, removeValue]
}

// 缓存Hook
export const useCache = <T>(key: string, ttl?: number) => {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(
    async (fetcher: () => Promise<T>) => {
      setLoading(true)
      setError(null)

      try {
        // 先检查缓存
        const cachedData = storageService.getCache(key)
        if (cachedData) {
          setData(cachedData)
          setLoading(false)
          return cachedData
        }

        // 缓存不存在，获取新数据
        const freshData = await fetcher()
        storageService.setCache(key, freshData, ttl)
        setData(freshData)
        setLoading(false)
        return freshData
      } catch (err) {
        const error = err instanceof Error ? err : new Error('获取数据失败')
        setError(error)
        setLoading(false)
        throw error
      }
    },
    [key, ttl]
  )

  const invalidate = useCallback(() => {
    storageService.removeCache(key)
    setData(null)
  }, [key])

  const prefetch = useCallback(
    async (fetcher: () => Promise<T>) => {
      try {
        const cachedData = storageService.getCache(key)
        if (cachedData) return

        const freshData = await fetcher()
        storageService.setCache(key, freshData, ttl)
      } catch (error) {
        console.warn('预取数据失败:', error)
      }
    },
    [key, ttl]
  )

  return {
    data,
    loading,
    error,
    fetch,
    invalidate,
    prefetch,
  }
}

// 持久化状态Hook
export const usePersistedState = <T>(
  key: string,
  initialValue: T,
  options?: {
    storage?: 'local' | 'session'
    serialize?: (value: T) => string
    deserialize?: (value: string) => T
  }
) => {
  const {
    storage = 'local',
    serialize = JSON.stringify,
    deserialize = JSON.parse,
  } = options || {}

  const [state, setState] = useState<T>(() => {
    try {
      const storageObj = storage === 'local' ? localStorage : sessionStorage
      const item = storageObj.getItem(key)
      return item !== null ? deserialize(item) : initialValue
    } catch (error) {
      console.error(`获取持久化状态 ${key} 失败:`, error)
      return initialValue
    }
  })

  useEffect(() => {
    try {
      const storageObj = storage === 'local' ? localStorage : sessionStorage
      storageObj.setItem(key, serialize(state))
    } catch (error) {
      console.error(`设置持久化状态 ${key} 失败:`, error)
    }
  }, [key, state, storage, serialize])

  return [state, setState] as const
}

export default useLocalStorage