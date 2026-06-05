import { useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router-dom"
import { LogIn } from "lucide-react"
import { useAuth } from "../../auth/AuthContext"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../../components/ui/Card"
import { Button } from "../../components/ui/Button"
import { Input } from "../../components/ui/Input"

type ScopeMode = "pharma" | "research"

export default function LoginPage() {
  const { login, error, loading } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [scope, setScope] = useState<ScopeMode>("pharma")
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({})

  function validate() {
    const errs: { username?: string; password?: string } = {}
    if (!username.trim()) errs.username = "Username is required"
    if (!password) errs.password = "Password is required"
    else if (password.length < 6) errs.password = "Password must be at least 6 characters"
    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!validate()) return
    try {
      await login(username, password, scope)
      navigate(scope === "research" ? "/dashboard/research" : "/dashboard/pharma", { replace: true })
    } catch {
      // error is set by context
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--clr-gray-10)] px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="items-center text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--clr-brand)]">
            <LogIn className="h-6 w-6 text-[var(--clr-text-inverse)]" />
          </div>
          <CardTitle>Welcome back</CardTitle>
          <CardDescription>Sign in to your account to continue</CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--clr-text-primary)]">
                Username
              </label>
              <Input
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={e => { setUsername(e.target.value); setFieldErrors(prev => ({ ...prev, username: undefined })) }}
                disabled={loading}
                className={fieldErrors.username ? "border-[var(--clr-border-error)]" : ""}
              />
              {fieldErrors.username && (
                <p className="mt-1 text-xs text-[var(--clr-error)]">{fieldErrors.username}</p>
              )}
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--clr-text-primary)]">
                Password
              </label>
              <Input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={e => { setPassword(e.target.value); setFieldErrors(prev => ({ ...prev, password: undefined })) }}
                disabled={loading}
                className={fieldErrors.password ? "border-[var(--clr-border-error)]" : ""}
              />
              {fieldErrors.password && (
                <p className="mt-1 text-xs text-[var(--clr-error)]">{fieldErrors.password}</p>
              )}
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--clr-text-primary)]">
                Login Mode
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setScope("pharma")}
                  disabled={loading}
                  className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    scope === "pharma"
                      ? "bg-[var(--clr-brand)] text-[var(--clr-text-inverse)]"
                      : "bg-[var(--clr-gray-20)] text-[var(--clr-text-secondary)] hover:bg-[var(--clr-gray-30)]"
                  }`}
                >
                  Pharma
                </button>
                <button
                  type="button"
                  onClick={() => setScope("research")}
                  disabled={loading}
                  className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    scope === "research"
                      ? "bg-[var(--clr-brand)] text-[var(--clr-text-inverse)]"
                      : "bg-[var(--clr-gray-20)] text-[var(--clr-text-secondary)] hover:bg-[var(--clr-gray-30)]"
                  }`}
                >
                  Research
                </button>
              </div>
            </div>

            {error && (
              <div className="rounded-md bg-red-50 px-3 py-2 text-xs text-[var(--clr-error)]">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" size="lg" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </Button>
          </form>
        </CardContent>

        <CardFooter className="justify-center">
          <p className="text-sm text-[var(--clr-text-secondary)]">
            Don&apos;t have an account?{" "}
            <Link to="/register" className="font-medium text-[var(--clr-brand)] hover:underline">
              Create one
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
