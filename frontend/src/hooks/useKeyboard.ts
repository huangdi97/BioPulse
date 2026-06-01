import { useEffect, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

interface ShortcutHandlers {
  onGlobalSearch?: () => void
  onEscape?: () => void
  onNew?: () => void
  onRefresh?: () => void
}

export function useKeyboard({
  onGlobalSearch,
  onEscape,
  onNew,
  onRefresh,
}: ShortcutHandlers = {}) {
  const navigate = useNavigate()
  const location = useLocation()

  const isListPage = () => {
    const pages = [
      '/hcps',
      '/tasks',
      '/scenarios',
      '/sessions',
      '/opport',
      '/bidding',
      '/contacts',
      '/notes',
      '/objections',
      '/visits',
      '/assessments',
      '/reflections',
      '/manager/visits',
    ]
    return pages.some((p) => location.pathname.includes(p))
  }

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey
      const target = e.target as HTMLElement
      const isInput =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable

      if (mod && e.key === 'k') {
        e.preventDefault()
        onGlobalSearch?.()
        return
      }

      if (e.key === 'Escape') {
        if (onEscape) {
          e.preventDefault()
          onEscape()
        } else {
          navigate(-1)
        }
        return
      }

      if (!isInput && isListPage()) {
        if (e.key === 'n' || e.key === 'N') {
          e.preventDefault()
          onNew?.()
          return
        }

        if (e.key === 'r' || e.key === 'R') {
          e.preventDefault()
          if (onRefresh) {
            onRefresh()
          } else {
            window.location.reload()
          }
        }
      }
    },
    [navigate, location.pathname, onGlobalSearch, onEscape, onNew, onRefresh]
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])
}
