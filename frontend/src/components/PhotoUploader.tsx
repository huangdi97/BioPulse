import { useCallback, useEffect, useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { Plus, X } from 'lucide-react'

const MAX_FILE_SIZE = 5 * 1024 * 1024
const DEFAULT_MAX_COUNT = 9

interface PhotoUploaderProps {
  photos: File[]
  onPhotosChange: (files: File[]) => void
  maxCount?: number
}

export default function PhotoUploader({
  photos,
  onPhotosChange,
  maxCount = DEFAULT_MAX_COUNT,
}: PhotoUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [previews, setPreviews] = useState<string[]>([])
  const [dragOver, setDragOver] = useState(false)

  const remaining = maxCount - photos.length

  useEffect(() => {
    const urls = photos.map((f) => URL.createObjectURL(f))
    setPreviews(urls)
    return () => urls.forEach((u) => URL.revokeObjectURL(u))
  }, [photos])

  const addFiles = useCallback(
    (files: FileList | File[]) => {
      const list = Array.from(files)
      const valid: File[] = []
      for (const f of list) {
        if (valid.length >= remaining) break
        if (!f.type.startsWith('image/')) continue
        if (f.size > MAX_FILE_SIZE) continue
        valid.push(f)
      }
      if (valid.length === 0) return
      onPhotosChange([...photos, ...valid])
    },
    [photos, remaining, onPhotosChange]
  )

  const removeFile = useCallback(
    (index: number) => {
      onPhotosChange(photos.filter((_, i) => i !== index))
    },
    [photos, onPhotosChange]
  )

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        addFiles(e.target.files)
        e.target.value = ''
      }
    },
    [addFiles]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      if (e.dataTransfer.files) {
        addFiles(e.dataTransfer.files)
      }
    },
    [addFiles]
  )

  return (
    <Card>
      <CardContent className="p-4 space-y-4">
        <div
          className={cn(
            'relative flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 transition-colors',
            dragOver
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          )}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <p className="text-sm text-muted-foreground">将照片拖拽到此处</p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={remaining <= 0}
            onClick={() => inputRef.current?.click()}
          >
            <Plus className="mr-1 h-4 w-4" />
            选择照片
          </Button>
          <p className="text-xs text-muted-foreground">
            支持 JPG / PNG / WebP，单张不超过 5MB
          </p>
          {photos.length > 0 && (
            <p className="text-xs text-muted-foreground">
              已选 {photos.length} 张，还可选 {remaining} 张
            </p>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={handleInputChange}
          />
        </div>

        {previews.length > 0 && (
          <div className="grid grid-cols-3 gap-3">
            {previews.map((url, i) => (
              <div key={`${photos[i]?.name ?? i}-${i}`} className="relative group aspect-square">
                <img
                  src={url}
                  alt={photos[i]?.name ?? ''}
                  className="h-full w-full rounded-md object-cover"
                />
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    removeFile(i)
                  }}
                  className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-destructive-foreground opacity-0 transition-opacity group-hover:opacity-100"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
