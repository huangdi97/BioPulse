import { Link } from "react-router-dom"
import { Button } from "../../components/ui/Button"
import { FileQuestion } from "lucide-react"

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-muted-foreground gap-4">
      <FileQuestion className="h-16 w-16 text-muted-foreground/50" />
      <h1 className="text-2xl font-bold text-foreground">Page Not Found</h1>
      <p className="text-sm">The page you are looking for does not exist.</p>
      <Button variant="link" asChild>
        <Link to="/dashboard/pharma">Back to Home</Link>
      </Button>
    </div>
  )
}
