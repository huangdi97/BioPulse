import { forwardRef, type InputHTMLAttributes } from "react"
import { cn } from "../../lib/utils"

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-9 w-full rounded-md border border-[var(--clr-border-default)] bg-[var(--clr-white)] px-3 py-1 text-sm text-[var(--clr-text-primary)] transition-colors placeholder:text-[var(--clr-text-placeholder)] focus-visible:outline-none focus-visible:border-[var(--clr-border-focus)] focus-visible:ring-1 focus-visible:ring-[var(--clr-border-focus)] disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
