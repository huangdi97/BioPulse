import { type HTMLAttributes } from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-[var(--radius-pill)] px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-[var(--clr-brand-light)] text-[var(--clr-brand)]",
        success: "bg-[var(--clr-success)]/15 text-[var(--clr-success)]",
        warning: "bg-[var(--clr-warning)]/15 text-[var(--clr-warning)]",
        error: "bg-[var(--clr-error)]/15 text-[var(--clr-error)]",
        neutral: "bg-[var(--clr-gray-10)] text-[var(--clr-gray-70)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
