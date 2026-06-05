import { forwardRef, type ButtonHTMLAttributes } from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--clr-border-focus)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[var(--clr-brand)] text-[var(--clr-text-inverse)] hover:bg-[var(--clr-brand-hover)]",
        secondary: "bg-[var(--clr-gray-20)] text-[var(--clr-text-primary)] hover:bg-[var(--clr-gray-30)]",
        outline: "border border-[var(--clr-border-default)] bg-[var(--clr-white)] hover:bg-[var(--clr-surface-hover)]",
        ghost: "hover:bg-[var(--clr-surface-hover)] text-[var(--clr-text-secondary)]",
        danger: "bg-[var(--clr-error)] text-[var(--clr-text-inverse)] hover:opacity-90",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-9 px-4",
        lg: "h-10 px-6",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
)

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
