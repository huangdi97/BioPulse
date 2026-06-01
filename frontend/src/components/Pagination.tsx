import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  pageSize?: number
  onPageSizeChange?: (size: number) => void
  pageSizeOptions?: number[]
  className?: string
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  pageSize,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 50],
  className,
}: PaginationProps) {
  if (totalPages <= 1) return null

  const pages: (number | 'ellipsis-start' | 'ellipsis-end')[] = []
  const delta = 2

  for (let i = 1; i <= totalPages; i++) {
    if (
      i === 1 ||
      i === totalPages ||
      (i >= currentPage - delta && i <= currentPage + delta)
    ) {
      pages.push(i)
    } else if (pages[pages.length - 1] !== 'ellipsis-start' && i < currentPage - delta) {
      pages.push('ellipsis-start')
    } else if (pages[pages.length - 1] !== 'ellipsis-end' && i > currentPage + delta) {
      pages.push('ellipsis-end')
    }
  }

  return (
    <div className={cn('flex items-center justify-between gap-4', className)}>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={currentPage <= 1}
          onClick={() => onPageChange(currentPage - 1)}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          上一页
        </Button>

        <div className="flex items-center gap-1">
          {pages.map((page, idx) => {
            if (typeof page === 'string') {
              return (
                <span
                  key={page + idx}
                  className="px-2 text-sm text-muted-foreground"
                >
                  ...
                </span>
              )
            }
            return (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                className={cn(
                  'h-8 w-8 rounded-md text-sm font-medium transition-colors',
                  page === currentPage
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted text-foreground'
                )}
              >
                {page}
              </button>
            )
          })}
        </div>

        <Button
          variant="outline"
          size="sm"
          disabled={currentPage >= totalPages}
          onClick={() => onPageChange(currentPage + 1)}
        >
          下一页
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>

      {pageSize !== undefined && onPageSizeChange && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">每页</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
          <span className="text-sm text-muted-foreground">条</span>
        </div>
      )}
    </div>
  )
}
