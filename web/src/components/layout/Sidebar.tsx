import { NavLink } from "react-router-dom"
import {
  Pill,
  FlaskConical,
  ShieldCheck,
  GraduationCap,
  TrendingUp,
  Settings,
  DollarSign,
  X,
} from "lucide-react"
import { cn } from "../../lib/utils"

const navItems = [
  { to: "/dashboard/pharma", label: "Pharma", icon: Pill },
  { to: "/dashboard/research", label: "Research", icon: FlaskConical },
  { to: "/compliance/overview", label: "Compliance", icon: ShieldCheck },
  { to: "/coach/training", label: "Training", icon: GraduationCap },
  { to: "/intel/analysis", label: "Analysis", icon: TrendingUp },
  { to: "/settings/system", label: "System", icon: Settings },
  { to: "/pricing", label: "定价方案", icon: DollarSign },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 h-full w-60 bg-[var(--clr-gray-100)] text-[var(--clr-text-inverse)] flex flex-col z-50 transition-transform duration-300",
          "md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
      <div className="flex items-center justify-between px-5 h-16 border-b border-[var(--clr-gray-70)]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-[var(--clr-brand)] flex items-center justify-center text-xs font-bold">
            Y
          </div>
          <span className="font-semibold text-sm tracking-wide">BioPulse</span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="md:hidden p-1 rounded hover:bg-[var(--clr-gray-90)] transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <nav className="flex-1 py-4 space-y-1 px-3">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-[var(--clr-gray-90)] text-[var(--clr-brand-light)]"
                  : "text-[var(--clr-gray-30)] hover:bg-[var(--clr-gray-90)] hover:text-[var(--clr-white)]"
              )
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-[var(--clr-gray-70)] text-xs text-[var(--clr-gray-50)]">
        v1.0.0
      </div>
    </aside>
    </>
  )
}
