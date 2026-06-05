import { useState, useMemo, type FormEvent } from "react"
import { Link, useNavigate } from "react-router-dom"
import { UserPlus } from "lucide-react"
import { useAuth } from "../../auth/AuthContext"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../../components/ui/Card"
import { Button } from "../../components/ui/Button"
import { Input } from "../../components/ui/Input"
import { Badge } from "../../components/ui/Badge"

function getStrength(password: string): { label: string; variant: "error" | "warning" | "success"; score: number } {
  let score = 0
  if (password.length >= 6) score++
  if (password.length >= 10) score++
  if (/[A-Z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  if (score <= 2) return { label: "Weak", variant: "error", score }
  if (score <= 3) return { label: "Medium", variant: "warning", score: 3 }
  return { label: "Strong", variant: "success", score: 5 }
}

export default function RegisterPage() {
  const { register, error, loading } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string; confirm?: string }>({})

  const strength = useMemo(() => getStrength(password), [password])

  function validate() {
    const errs: { username?: string; password?: string; confirm?: string } = {}
    if (!username.trim()) errs.username = "Username is required"
    else if (username.trim().length < 3) errs.username = "Username must be at least 3 characters"
    if (!password) errs.password = "Password is required"
    else if (password.length < 6) errs.password = "Password must be at least 6 characters"
    if (!confirm) errs.confirm = "Please confirm your password"
    else if (password !== confirm) errs.confirm = "Passwords do not match"
    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!validate()) return
    try {
      await register(username, password)
      navigate("/dashboard/pharma", { replace: true })
    } catch {
      // error is set by context
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--clr-gray-10)] px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="items-center text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--clr-brand)]">
            <UserPlus className="h-6 w-6 text-[var(--clr-text-inverse)]" />
          </div>
          <CardTitle>Create an account</CardTitle>
          <CardDescription>Sign up to get started</CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--clr-text-primary)]">
                Username
              </label>
              <Input
                type="text"
                placeholder="Choose a username"
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
                placeholder="Create a password"
                value={password}
                onChange={e => { setPassword(e.target.value); setFieldErrors(prev => ({ ...prev, password: undefined })) }}
                disabled={loading}
                className={fieldErrors.password ? "border-[var(--clr-border-error)]" : ""}
              />
              {password.length > 0 && (
                <div className="mt-1.5 flex items-center gap-2">
                  <div className="flex h-1.5 flex-1 gap-0.5">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div
                        key={i}
                        className={`h-full flex-1 rounded-full ${
                          i < strength.score
                            ? strength.variant === "error"
                              ? "bg-[var(--clr-error)]"
                              : strength.variant === "warning"
                                ? "bg-[var(--clr-warning)]"
                                : "bg-[var(--clr-success)]"
                            : "bg-[var(--clr-border-subtle)]"
                        }`}
                      />
                    ))}
                  </div>
                  <Badge variant={strength.variant}>{strength.label}</Badge>
                </div>
              )}
              {fieldErrors.password && (
                <p className="mt-1 text-xs text-[var(--clr-error)]">{fieldErrors.password}</p>
              )}
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-[var(--clr-text-primary)]">
                Confirm Password
              </label>
              <Input
                type="password"
                placeholder="Repeat your password"
                value={confirm}
                onChange={e => { setConfirm(e.target.value); setFieldErrors(prev => ({ ...prev, confirm: undefined })) }}
                disabled={loading}
                className={fieldErrors.confirm ? "border-[var(--clr-border-error)]" : ""}
              />
              {fieldErrors.confirm && (
                <p className="mt-1 text-xs text-[var(--clr-error)]">{fieldErrors.confirm}</p>
              )}
            </div>

            {error && (
              <div className="rounded-md bg-red-50 px-3 py-2 text-xs text-[var(--clr-error)]">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" size="lg" disabled={loading}>
              {loading ? "Creating account..." : "Create account"}
            </Button>
          </form>
        </CardContent>

        <CardFooter className="justify-center">
          <p className="text-sm text-[var(--clr-text-secondary)]">
            Already have an account?{" "}
            <Link to="/login" className="font-medium text-[var(--clr-brand)] hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
