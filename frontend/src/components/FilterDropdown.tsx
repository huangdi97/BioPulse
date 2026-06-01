import { useState, useEffect, useRef } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface FilterOption {
  value: string
  label: string
}

interface FilterDropdownProps {
  label: string
  value: string | string[]
  options: string[] | FilterOption[]
  onChange: (value: string) => void
  onChangeMulti?: (values: string[]) => void
  className?: string
}

export function FilterDropdown({
  label,
  value,
  options,
  onChange,
  onChangeMulti,
  className,
}: FilterDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const isMulti = onChangeMulti !== undefined

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const normalizedOptions: FilterOption[] = Array.isArray(options) && options.length > 0
    ? (typeof options[0] === 'string'
      ? (options as string[]).map((v) => ({ value: v, label: v }))
      : options as FilterOption[])
    : []

  const displayLabel = isMulti
    ? (value as string[]).length > 0
      ? `${label}: ${(value as string[]).length}项`
      : label
    : (() => {
        const match = normalizedOptions.find((o) => o.value === value)
        return match ? `${label}: ${match.label}` : `${label}: ${value}`
      })()

  const handleClick = (opt: FilterOption) => {
    if (isMulti) {
      const selected = value as string[]
      const next = selected.includes(opt.value)
        ? selected.filter((v) => v !== opt.value)
        : [...selected, opt.value]
      onChangeMulti!(next)
    } else {
      onChange(opt.value)
      setOpen(false)
    }
  }

  const isSelected = (v: string) =>
    isMulti ? (value as string[]).includes(v) : value === v

  return (
    <div ref={ref} className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 h-9 px-3 rounded-md border border-input bg-background text-sm hover:bg-accent hover:text-accent-foreground"
      >
        <span className="text-muted-foreground">{displayLabel}</span>
        <ChevronDown className="h-3 w-3 text-muted-foreground" />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 z-50 min-w-[140px] rounded-md border bg-popover shadow-md max-h-60 overflow-y-auto">
          {normalizedOptions.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleClick(opt)}
              className={cn(
                'w-full flex items-center gap-2 text-left px-3 py-1.5 text-sm hover:bg-accent rounded-sm',
                isSelected(opt.value) && 'font-medium bg-accent'
              )}
            >
              {isMulti && (
                <span
                  className={cn(
                    'flex h-4 w-4 shrink-0 items-center justify-center rounded border',
                    isSelected(opt.value)
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-muted-foreground/30'
                  )}
                >
                  {isSelected(opt.value) && <Check className="h-3 w-3" />}
                </span>
              )}
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
