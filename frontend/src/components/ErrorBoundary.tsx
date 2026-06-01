import { Component, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }
      return (
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-50 mb-4">
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
          <h3 className="text-lg font-medium text-foreground mb-1">
            页面加载失败
          </h3>
          <p className="text-sm text-muted-foreground max-w-sm mb-4">
            {this.state.error?.message || '发生了未知错误'}
          </p>
          <Button onClick={this.handleRetry} size="sm" variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            重试
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
