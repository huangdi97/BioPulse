import json
import os
from pathlib import Path


def hex_to_hsl(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    l_val = (mx + mn) / 2.0

    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2.0 - mx - mn) if l_val > 0.5 else d / (mx + mn)
        if mx == r:
            h = (g - b) / d + (6.0 if g < b else 0.0)
        elif mx == g:
            h = (b - r) / d + 2.0
        else:
            h = (r - g) / d + 4.0
        h /= 6.0

    hue = round(h * 360)
    sat = round(s * 100)
    lit = round(l_val * 100)
    return f"{hue} {sat}% {lit}%"


def load_tokens(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


TOKENS_PATH = Path(__file__).resolve().parent.parent / "design-tokens" / "tokens.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "frontend" / "src" / "styles" / "tokens.css"


tokens = load_tokens(str(TOKENS_PATH))
c = tokens["colors"]
t = tokens["typography"]
s = tokens["spacing"]
br = tokens["border_radius"]
sh = tokens.get("shadow", {})


def hsl(hex_val):
    return hex_to_hsl(hex_val)


light_vars = {}
dark_vars = {}

# Shadcn core variable mapping
shadcn_light = {
    "--background": hsl(c["neutral"]["white"]),
    "--foreground": hsl(c["text"]["primary"]),
    "--card": hsl(c["surface"]["page"]),
    "--card-foreground": hsl(c["text"]["primary"]),
    "--popover": hsl(c["surface"]["page"]),
    "--popover-foreground": hsl(c["text"]["primary"]),
    "--primary": hsl(c["brand"]["primary"]),
    "--primary-foreground": hsl(c["text"]["inverse"]),
    "--secondary": hsl(c["neutral"]["gray_20"]),
    "--secondary-foreground": hsl(c["text"]["primary"]),
    "--muted": hsl(c["neutral"]["gray_10"]),
    "--muted-foreground": hsl(c["text"]["secondary"]),
    "--accent": hsl(c["brand"]["primary_light"]),
    "--accent-foreground": hsl(c["brand"]["primary"]),
    "--destructive": hsl(c["status"]["error"]),
    "--destructive-foreground": hsl(c["text"]["inverse"]),
    "--border": hsl(c["border"]["default"]),
    "--input": hsl(c["border"]["input"]),
    "--ring": hsl(c["brand"]["primary"]),
}

shadcn_dark = {
    "--background": hsl(c["neutral"]["gray_100"]),
    "--foreground": hsl(c["text"]["inverse"]),
    "--card": hsl(c["neutral"]["gray_90"]),
    "--card-foreground": hsl(c["text"]["inverse"]),
    "--popover": hsl(c["neutral"]["gray_90"]),
    "--popover-foreground": hsl(c["text"]["inverse"]),
    "--primary": hsl(c["brand"]["primary"]),
    "--primary-foreground": hsl(c["text"]["primary"]),
    "--secondary": hsl(c["neutral"]["gray_70"]),
    "--secondary-foreground": hsl(c["text"]["inverse"]),
    "--muted": hsl(c["neutral"]["gray_70"]),
    "--muted-foreground": hsl(c["neutral"]["gray_30"]),
    "--accent": hsl(c["brand"]["primary"]),
    "--accent-foreground": hsl(c["text"]["inverse"]),
    "--destructive": hsl(c["status"]["error"]),
    "--destructive-foreground": hsl(c["text"]["inverse"]),
    "--border": hsl(c["neutral"]["gray_70"]),
    "--input": hsl(c["neutral"]["gray_70"]),
    "--ring": hsl(c["brand"]["primary"]),
}

light_vars.update(shadcn_light)
dark_vars.update(shadcn_dark)

# Text tokens
light_vars["--color-text-primary"] = hsl(c["text"]["primary"])
light_vars["--color-text-secondary"] = hsl(c["text"]["secondary"])
light_vars["--color-text-placeholder"] = hsl(c["text"]["placeholder"])
light_vars["--color-text-disabled"] = hsl(c["text"]["disabled"])
light_vars["--color-text-inverse"] = hsl(c["text"]["inverse"])

dark_vars["--color-text-primary"] = hsl(c["text"]["inverse"])
dark_vars["--color-text-secondary"] = hsl(c["neutral"]["gray_30"])
dark_vars["--color-text-placeholder"] = hsl(c["neutral"]["gray_50"])
dark_vars["--color-text-disabled"] = hsl(c["neutral"]["gray_60"])
dark_vars["--color-text-inverse"] = hsl(c["text"]["primary"])

# Brand tokens
light_vars["--color-brand-primary"] = hsl(c["brand"]["primary"])
light_vars["--color-brand-primary-hover"] = hsl(c["brand"]["primary_hover"])
light_vars["--color-brand-primary-active"] = hsl(c["brand"]["primary_active"])
light_vars["--color-brand-primary-light"] = hsl(c["brand"]["primary_light"])

for k in ("--color-brand-primary", "--color-brand-primary-hover", "--color-brand-primary-active", "--color-brand-primary-light"):
    dark_vars[k] = light_vars[k]

# Surface tokens
light_vars["--color-surface-page"] = hsl(c["surface"]["page"])
light_vars["--color-surface-card"] = hsl(c["surface"]["card"])
light_vars["--color-surface-card-alt"] = hsl(c["surface"]["card_alt"])
light_vars["--color-surface-hover"] = hsl(c["surface"]["hover"])
light_vars["--color-surface-selected"] = hsl(c["surface"]["selected"])

dark_vars["--color-surface-page"] = hsl(c["neutral"]["gray_100"])
dark_vars["--color-surface-card"] = hsl(c["neutral"]["gray_90"])
dark_vars["--color-surface-card-alt"] = hsl(c["neutral"]["gray_70"])
dark_vars["--color-surface-hover"] = hsl(c["neutral"]["gray_70"])
dark_vars["--color-surface-selected"] = hsl(c["neutral"]["gray_60"])

# Border tokens
light_vars["--color-border-default"] = hsl(c["border"]["default"])
light_vars["--color-border-subtle"] = hsl(c["border"]["subtle"])
light_vars["--color-border-input"] = hsl(c["border"]["input"])
light_vars["--color-border-focus"] = hsl(c["border"]["focus"])
light_vars["--color-border-error"] = hsl(c["border"]["error"])

dark_vars["--color-border-default"] = hsl(c["neutral"]["gray_70"])
dark_vars["--color-border-subtle"] = hsl(c["neutral"]["gray_60"])
dark_vars["--color-border-input"] = hsl(c["neutral"]["gray_60"])
dark_vars["--color-border-focus"] = hsl(c["brand"]["primary"])
dark_vars["--color-border-error"] = hsl(c["status"]["error"])

# Status tokens
for name, hex_val in c["status"].items():
    light_vars[f"--color-status-{name}"] = hsl(hex_val)
    dark_vars[f"--color-status-{name}"] = hsl(hex_val)

# Mode tokens
for name, hex_val in c["mode"].items():
    light_vars[f"--color-mode-{name}"] = hsl(hex_val)
    dark_vars[f"--color-mode-{name}"] = hsl(hex_val)

# Neutral tokens (as HSL)
for name, hex_val in c["neutral"].items():
    css_name = name.replace("gray_", "gray-")
    light_vars[f"--color-neutral-{css_name}"] = hsl(hex_val)
    dark_vars[f"--color-neutral-{css_name}"] = hsl(hex_val)

# Spacing tokens
for name, val in s.items():
    if name == "unit":
        continue
    light_vars[f"--spacing-{name}"] = f"{val}px"
    dark_vars[f"--spacing-{name}"] = f"{val}px"

# Border radius
light_vars["--radius"] = f"{br['md']}px"
for name, val in br.items():
    if val == 9999:
        light_vars[f"--radius-{name}"] = "9999px"
        dark_vars[f"--radius-{name}"] = "9999px"
    else:
        light_vars[f"--radius-{name}"] = f"{val}px"
        dark_vars[f"--radius-{name}"] = f"{val}px"

dark_vars["--radius"] = f"{br['md']}px"

# Font family
light_vars["--font-family-primary"] = f"'{t['font_family']['primary']}', sans-serif"
light_vars["--font-family-mono"] = f"'{t['font_family']['mono']}', monospace"
dark_vars["--font-family-primary"] = light_vars["--font-family-primary"]
dark_vars["--font-family-mono"] = light_vars["--font-family-mono"]

# Shadow tokens (keep as-is, not HSL)
for name, val in sh.items():
    light_vars[f"--shadow-{name}"] = val
    dark_vars[f"--shadow-{name}"] = val


def format_vars(vars_dict: dict, indent: int = 2) -> str:
    pad = "  " * indent
    lines = []
    for key in sorted(vars_dict):
        lines.append(f"{pad}{key}: {vars_dict[key]};")
    return "\n".join(lines)


os.makedirs(OUTPUT_PATH.parent, exist_ok=True)

css_content = f"""/* Auto-generated from design-tokens/tokens.json — do not edit manually */
/* Run: python scripts/generate_tokens_css.py */

:root {{
{format_vars(light_vars)}
}}

.dark {{
{format_vars(dark_vars)}
}}
"""

with open(OUTPUT_PATH, "w") as f:
    f.write(css_content)

print(f"✅ Generated {OUTPUT_PATH}")
print(f"   Light vars: {len(light_vars)}")
print(f"   Dark vars:  {len(dark_vars)}")
