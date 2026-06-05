import { useState, useRef, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Bell, Search, ChevronDown, User, Settings, LogOut } from "lucide-react"
import { useAuth } from "../../auth/AuthContext"

export default function TopNav() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    if (dropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [dropdownOpen])

  const handleLogout = () => {
    logout()
    navigate("/login", { replace: true })
  }

  const username = user?.username ?? "User"
  const initial = username.charAt(0).toUpperCase()

  return (
    <header className="sticky top-0 h-16 bg-[var(--clr-white)] border-b border-[var(--clr-border-default)] flex items-center justify-between px-6 z-40">
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <Search className="w-4 h-4 text-[var(--clr-text-placeholder)]" />
        <input
          type="text"
          placeholder="Search..."
          className="flex-1 bg-transparent border-none outline-none text-sm text-[var(--clr-text-primary)] placeholder:text-[var(--clr-text-placeholder)]"
        />
      </div>

      <div className="flex items-center gap-4">
        <button
          type="button"
          className="relative p-2 rounded-md text-[var(--clr-text-secondary)] hover:bg-[var(--clr-surface-hover)] transition-colors"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[var(--clr-error)]" />
        </button>

        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 pl-4 pr-1 py-1 border-l border-[var(--clr-border-default)] hover:bg-[var(--clr-surface-hover)] rounded-md transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-[var(--clr-brand)] flex items-center justify-center text-[var(--clr-white)] text-xs font-semibold shrink-0">
              {initial}
            </div>
            <div className="text-sm text-left">
              <p className="font-medium text-[var(--clr-text-primary)] leading-tight">
                {username}
              </p>
              <p className="text-xs text-[var(--clr-text-secondary)]">
                {user?.username ? `${user.username}@yysd.io` : ""}
              </p>
            </div>
            <ChevronDown className="w-4 h-4 text-[var(--clr-text-secondary)]" />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 top-full mt-1 w-44 bg-[var(--clr-white)] border border-[var(--clr-border-default)] rounded-md shadow-[var(--shadow-modal)] z-50 py-1">
              <button
                type="button"
                onClick={() => { setDropdownOpen(false); navigate("/settings/system") }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--clr-text-primary)] hover:bg-[var(--clr-surface-hover)] transition-colors"
              >
                <User className="w-4 h-4" />
                个人中心
              </button>
              <button
                type="button"
                onClick={() => { setDropdownOpen(false); navigate("/settings/system") }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--clr-text-primary)] hover:bg-[var(--clr-surface-hover)] transition-colors"
              >
                <Settings className="w-4 h-4" />
                设置
              </button>
              <div className="border-t border-[var(--clr-border-default)] my-1" />
              <button
                type="button"
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--clr-error)] hover:bg-[var(--clr-surface-hover)] transition-colors"
              >
                <LogOut className="w-4 h-4" />
                登出
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
