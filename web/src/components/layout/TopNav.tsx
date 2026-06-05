import { Bell, Search } from "lucide-react"

export default function TopNav() {
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

        <div className="flex items-center gap-3 pl-4 border-l border-[var(--clr-border-default)]">
          <div className="w-8 h-8 rounded-full bg-[var(--clr-brand)] flex items-center justify-center text-[var(--clr-white)] text-xs font-semibold">
            U
          </div>
          <div className="text-sm">
            <p className="font-medium text-[var(--clr-text-primary)] leading-tight">
              Admin
            </p>
            <p className="text-xs text-[var(--clr-text-secondary)]">
              admin@yysd.io
            </p>
          </div>
        </div>
      </div>
    </header>
  )
}
