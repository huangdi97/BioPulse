import { useState, useEffect, useRef } from 'react'
import { Input } from '@/components/ui/input'
import { Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SearchBarProps {
  placeholder?: string
  value: string
  onChange: (value: string) => void
  debounceMs?: number
  className?: string
}

export function SearchBar({
  placeholder = '搜索...',
  value,
  onChange,
  debounceMs = 300,
  className,
}: SearchBarProps) {
  const [local, setLocal] = useState(value)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    setLocal(value)
  }, [value])

  useEffect(() => {
    timerRef.current = setTimeout(() => {
      onChange(local)
    }, debounceMs)
    return () => clearTimeout(timerRef.current)
  }, [local, debounceMs, onChange])

  return (
    <div className={cn('relative', className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        placeholder={placeholder}
        value={local}
        onChange={(e) => setLocal(e.target.value)}
        className="pl-9 pr-9"
      />
      {local && (
        <button
          type="button"
          onClick={() => {
            setLocal('')
            onChange('')
          }}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
