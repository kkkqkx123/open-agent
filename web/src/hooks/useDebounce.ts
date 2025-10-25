import { useRef, useCallback, useEffect, useState } from 'react'

// 防抖Hook
export const useDebounce = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const timeoutRef = useRef<NodeJS.Timeout>()

  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      timeoutRef.current = setTimeout(() => {
        callback(...args)
      }, delay)
    },
    [callback, delay]
  ) as T

  // 清理函数
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return debouncedCallback
}

// 节流Hook
export const useThrottle = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const lastRunRef = useRef<number>(0)
  const timeoutRef = useRef<NodeJS.Timeout>()

  const throttledCallback = useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now()

      if (now - lastRunRef.current >= delay) {
        lastRunRef.current = now
        callback(...args)
      } else {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
        }

        timeoutRef.current = setTimeout(() => {
          lastRunRef.current = Date.now()
          callback(...args)
        }, delay - (now - lastRunRef.current))
      }
    },
    [callback, delay]
  ) as T

  // 清理函数
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return throttledCallback
}

// 防抖值Hook
export const useDebouncedValue = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

// 节流值Hook
export const useThrottledValue = <T>(value: T, delay: number): T => {
  const [throttledValue, setThrottledValue] = useState<T>(value)
  const lastExecuted = useRef<number>(Date.now())

  useEffect(() => {
    const handler = setTimeout(() => {
      const now = Date.now()
      if (now - lastExecuted.current >= delay) {
        setThrottledValue(value)
        lastExecuted.current = now
      }
    }, delay - (Date.now() - lastExecuted.current))

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return throttledValue
}

export default useDebounce