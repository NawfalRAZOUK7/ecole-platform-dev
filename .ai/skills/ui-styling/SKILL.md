---
name: ui-styling
description: Create beautiful, accessible user interfaces with shadcn/ui components (built on Radix UI + Tailwind), Tailwind CSS utility-first styling, and design-token-driven theming. Use when building UI in web/, implementing design systems, creating responsive layouts, adding accessible components (dialogs, dropdowns, forms, tables), customizing themes and colors, implementing dark mode, or establishing consistent styling patterns.
license: MIT
---

# UI Styling Skill

Comprehensive skill for creating beautiful, accessible user interfaces combining shadcn/ui components, Tailwind CSS utility styling, and consistent design tokens.

**Project note (Ecole Platform web/):** the React app currently uses plain CSS + custom design tokens (`design-tokens/`), react-hook-form + zod, lucide-react, framer-motion — no Tailwind/shadcn installed. The general principles (accessibility, responsive design, tokens, composition) apply as-is; the shadcn/Tailwind setup sections apply only if the team adopts those tools. Respect the existing design tokens before introducing new ones — see `docs/DESIGN_COHERENCE_ANALYSIS.md`.

## Reference

- shadcn/ui: https://ui.shadcn.com/llms.txt
- Tailwind CSS: https://tailwindcss.com/docs

## When to Use This Skill

- Building UI with React-based frameworks (Vite, Next.js, Remix)
- Implementing accessible components (dialogs, forms, tables, navigation)
- Styling with utility-first CSS approach
- Creating responsive, mobile-first layouts
- Implementing dark mode and theme customization
- Building design systems with consistent tokens
- Adding complex UI patterns (data tables, command palettes)

## Core Stack

### Component Layer: shadcn/ui
- Pre-built accessible components via Radix UI primitives
- Copy-paste distribution model (components live in your codebase)
- TypeScript-first with full type safety; CLI-based installation

### Styling Layer: Tailwind CSS
- Utility-first CSS framework, build-time processing, zero runtime overhead
- Mobile-first responsive design; consistent design tokens

## Quick Start

```bash
npx shadcn@latest init
npx shadcn@latest add button card dialog form
```

```tsx
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export function Dashboard() {
  return (
    <div className="container mx-auto p-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Analytics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">View your metrics</p>
          <Button variant="default" className="w-full">View Details</Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

**Tailwind-only (Vite):**
```bash
npm install -D tailwindcss @tailwindcss/vite
```
```javascript
// vite.config.ts
import tailwindcss from '@tailwindcss/vite'
export default { plugins: [tailwindcss()] }
```
```css
/* src/index.css */
@import "tailwindcss";
```

## Best Practices

1. **Component Composition**: build complex UIs from simple, composable primitives.
2. **Utility-First Styling**: use utility classes directly; extract components only for true repetition.
3. **Mobile-First Responsive**: start with mobile styles, layer responsive variants (`sm:`, `md:`, `lg:`, `xl:`).
4. **Accessibility-First**: leverage Radix primitives (or proper ARIA + semantic HTML), visible focus states, keyboard navigation, screen-reader announcements for dynamic content.
5. **Design Tokens**: consistent spacing scale, color palettes, typography system — single source of truth.
6. **Dark Mode Consistency**: apply dark variants to ALL themed elements, not just backgrounds.
7. **Performance**: leverage CSS purging; avoid dynamically constructed class names.
8. **TypeScript**: full type safety for better DX.
9. **Visual Hierarchy**: let composition guide attention; use spacing and color intentionally.

## Common Patterns

**Form with validation (react-hook-form + zod — already used in web/):**
```tsx
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
})

export function LoginForm() {
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" }
  })
  // render fields with labels bound via htmlFor/id, show errors inline,
  // aria-invalid on errored inputs, submit disabled while pending
}
```

**Responsive layout with dark mode:**
```tsx
<div className="min-h-screen bg-white dark:bg-gray-900">
  <div className="container mx-auto px-4 py-8">
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* cards */}
    </div>
  </div>
</div>
```

## Accessibility Checklist

- [ ] All interactive elements keyboard-reachable, logical tab order
- [ ] Visible focus indicator (never `outline: none` without replacement)
- [ ] Form inputs have associated labels; errors announced (aria-live / FormMessage)
- [ ] Color contrast ≥ 4.5:1 for text, 3:1 for large text/UI components
- [ ] Dialogs trap focus and restore it on close
- [ ] Touch targets ≥ 44x44px
- [ ] Images have alt text; icons that convey meaning have accessible names

## Resources

- shadcn/ui Docs: https://ui.shadcn.com
- Tailwind CSS Docs: https://tailwindcss.com
- Radix UI: https://radix-ui.com
- Headless UI: https://headlessui.com

---

*Source: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) ui-styling (MIT), trimmed: upstream reference files (shadcn-components, theming, accessibility, tailwind-*, canvas-design-system) and Python scripts not vendored — fetch from upstream if deep detail is needed. Project notes added for the existing non-Tailwind stack.*
