# Design System & Theming Strategy

## 1. Philosophy: "Premium & Moddable"

Our goal is to create an interface that feels like a high-end video game (Baldur's Gate 3 style) rather than a standard SaaS dashboard, while allowing complete visual overhauls (Mods).

### Core Principles
1.  **CSS Variables as the API:** Every color, spacing, radius, and font size must be a CSS variable. This is the "Modding API".
2.  **Scoped Complexity:** The App Shell handles the global theme. MFEs inherit it but can define local overrides if necessary (though discouraged for consistency).
3.  **shadcn/ui as the Base:** We use shadcn/ui for accessibility and functionality, but heavily customized visually.

---

## 2. Theming Engine (The "Modding API")

We will use a **3-Layer Variable System**:

### Layer 1: Primitive Tokens (The Palette)
Raw color values. Mods can change these to shift the entire color scheme.
```css
:root {
  /* HSL Values for runtime opacity manipulation */
  --palette-obsidian: 240 10% 4%;
  --palette-gold: 45 100% 50%;
  --palette-crimson: 0 100% 40%;
  --palette-parchment: 35 30% 90%;
}
```

### Layer 2: Semantic Tokens (The Usage)
Mapping primitives to UI roles. This is what components actually use.
```css
:root {
  --bg-app: hsl(var(--palette-obsidian));
  --bg-panel: hsl(var(--palette-obsidian) / 0.8); /* Glassmorphism */
  --text-primary: hsl(var(--palette-parchment));
  --accent-main: hsl(var(--palette-gold));
  --border-subtle: hsl(var(--palette-gold) / 0.2);
}
```

### Layer 3: Component Tokens (The Specifics)
Specific overrides for complex components.
```css
:root {
  --card-border-radius: 12px;
  --input-bg: rgba(0, 0, 0, 0.3);
}
```

---

## 3. Technology Stack

### Tailwind CSS Configuration
We will extend the Tailwind config to map directly to our Semantic Tokens.
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--bg-app))",
        panel: "hsl(var(--bg-panel))",
        accent: "hsl(var(--accent-main))",
        // ...
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"], // Default
        heading: ["Cinzel", "serif"], // For headers (Fantasy feel)
        mono: ["Fira Code", "monospace"], // For code/stats
      }
    }
  }
}
```

### shadcn/ui Customization
We will use the `new-york` style (smaller text, sharper borders) as a base, but override the `globals.css` completely.
- **Radius:** Default to slightly rounded (0.5rem) but moddable.
- **Animations:** Add custom keyframes for "fade-in-up" and "pulse-glow" to feel alive.

---

## 4. Modding Implementation

### How a Mod works
A "Mod" is simply a `.css` file that redefines the `:root` variables.

### Loading a Mod
1.  **Default:** `themes/default-dark-fantasy.css` is imported in `main.tsx`.
2.  **User Selection:** User selects "Sci-Fi Neon" in Settings.
3.  **Injection:** The App Shell injects `<link rel="stylesheet" href="/themes/scifi-neon.css">` which overrides the default variables.
4.  **Persistence:** Selection saved in `localStorage`.

---

## 5. Visual Assets & Icons

- **Icons:** `lucide-react` for UI icons (clean, modern).
- **Game Icons:** `game-icons.net` (SVG) for RPG specific things (swords, potions).
- **Fonts:**
  - **Headings:** *Cinzel* or *Uncial Antiqua* (Google Fonts) for the fantasy feel.
  - **Body:** *Inter* or *Outfit* for readability.

---

## 6. Implementation Plan

1.  **Setup `packages/ui`:** Create the shared UI library.
2.  **Install Tailwind & shadcn:** Configure `tailwind.config.js` and `components.json`.
3.  **Define `globals.css`:** Write the default "Dark Fantasy" variable set.
4.  **Create Core Components:** Button, Card, Input, Dialog (customized).
5.  **Create Theme Switcher:** A simple utility to swap CSS files for testing.
