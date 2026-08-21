import { useEffect, useRef } from 'react'

/**
 * usePolling(fn, interval, condition)
 *
 * Calls `fn()` every `interval` milliseconds while `condition` is true.
 * Automatically stops when `condition` becomes false or the component unmounts.
 *
 * @param {() => void} fn         - Async or sync callback to invoke on each tick.
 * @param {number}     interval   - Polling interval in milliseconds (e.g. 3000).
 * @param {boolean}    condition  - When false the interval is cleared.
 */
export default function usePolling(fn, interval, condition) {
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    if (!condition) return

    const id = setInterval(() => fnRef.current(), interval)
    return () => clearInterval(id)
  }, [condition, interval])
}
