import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          hover: "hsl(var(--color-brand-primary-hover))",
          active: "hsl(var(--color-brand-primary-active))",
          light: "hsl(var(--color-brand-primary-light))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        brand: {
          primary: "hsl(var(--color-brand-primary))",
          hover: "hsl(var(--color-brand-primary-hover))",
          active: "hsl(var(--color-brand-primary-active))",
          light: "hsl(var(--color-brand-primary-light))",
        },
        mode: {
          pharma: "hsl(var(--color-mode-pharma))",
          research: "hsl(var(--color-mode-research))",
          "compliance-warn": "hsl(var(--color-mode-compliance_warn))",
          "compliance-pass": "hsl(var(--color-mode-compliance_pass))",
        },
        status: {
          success: "hsl(var(--color-status-success))",
          error: "hsl(var(--color-status-error))",
          warning: "hsl(var(--color-status-warning))",
          info: "hsl(var(--color-status-info))",
        },
        neutral: {
          10: "hsl(var(--color-neutral-gray-10))",
          20: "hsl(var(--color-neutral-gray-20))",
          30: "hsl(var(--color-neutral-gray-30))",
          50: "hsl(var(--color-neutral-gray-50))",
          60: "hsl(var(--color-neutral-gray-60))",
          70: "hsl(var(--color-neutral-gray-70))",
          90: "hsl(var(--color-neutral-gray-90))",
          100: "hsl(var(--color-neutral-gray-100))",
          white: "hsl(var(--color-neutral-white))",
        },
        surface: {
          page: "hsl(var(--color-surface-page))",
          card: "hsl(var(--color-surface-card))",
          "card-alt": "hsl(var(--color-surface-card-alt))",
          hover: "hsl(var(--color-surface-hover))",
          selected: "hsl(var(--color-surface-selected))",
        },
        text: {
          primary: "hsl(var(--color-text-primary))",
          secondary: "hsl(var(--color-text-secondary))",
          placeholder: "hsl(var(--color-text-placeholder))",
          disabled: "hsl(var(--color-text-disabled))",
          inverse: "hsl(var(--color-text-inverse))",
        },
        border: {
          DEFAULT: "hsl(var(--color-border-default))",
          subtle: "hsl(var(--color-border-subtle))",
          input: "hsl(var(--color-border-input))",
          focus: "hsl(var(--color-border-focus))",
          error: "hsl(var(--color-border-error))",
        },
      },
      borderRadius: {
        lg: "var(--radius-lg)",
        md: "var(--radius-md)",
        sm: "var(--radius-sm)",
        xl: "var(--radius-xl)",
        pill: "var(--radius-pill)",
        none: "var(--radius-none)",
      },
      boxShadow: {
        border: "var(--shadow-border)",
        card: "var(--shadow-card)",
        raised: "var(--shadow-raised)",
        modal: "var(--shadow-modal)",
      },
      fontFamily: {
        sans: ["var(--font-family-primary)"],
        mono: ["var(--font-family-mono)"],
      },
      spacing: {
        xs: "var(--spacing-xs)",
        sm: "var(--spacing-sm)",
        md: "var(--spacing-md)",
        lg: "var(--spacing-lg)",
        xl: "var(--spacing-xl)",
        xxl: "var(--spacing-xxl)",
        xxxl: "var(--spacing-xxxl)",
        section: "var(--spacing-section)",
      },
    },
  },
  plugins: [],
}

export default config
