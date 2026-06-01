import { useState, useCallback } from 'react'
import { Outlet } from 'react-router-dom'
import { useKeyboard } from '@/hooks/useKeyboard'
import { GlobalSearchDialog } from '@/components/GlobalSearchDialog'

export default function KeyboardShell() {
  const [searchOpen, setSearchOpen] = useState(false)

  const handleGlobalSearch = useCallback(() => {
    setSearchOpen(true)
  }, [])

  useKeyboard({
    onGlobalSearch: handleGlobalSearch,
  })

  return (
    <>
      <GlobalSearchDialog open={searchOpen} onClose={() => setSearchOpen(false)} />
      <Outlet />
    </>
  )
}
