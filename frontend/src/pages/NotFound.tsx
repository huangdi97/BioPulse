import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { FileQuestion } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-muted-foreground gap-4">
      <FileQuestion className="h-16 w-16 text-muted-foreground/50" />
      <h1 className="text-2xl font-bold text-foreground">页面未找到</h1>
      <p className="text-sm">您访问的页面不存在或已被移除。</p>
      <Button variant="link" asChild>
        <Link to="/rep/dashboard">返回首页</Link>
      </Button>
    </div>
  )
}
