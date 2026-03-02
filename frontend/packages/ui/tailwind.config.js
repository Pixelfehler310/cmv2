/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: ["./src/**/*.{ts,tsx}"],
    theme: {
        container: {
            center: true,
            padding: "2rem",
            screens: {
                "2xl": "1400px",
            },
        },
        extend: {
            // VTT-specific semantic mappings (bridge between Tailwind utilities and design system tokens)
            colors: {
                // These map Tailwind's bg-background, text-foreground etc to design system tokens
                border: "var(--border-subtle)",
                input: "var(--bg-inset)",
                ring: "var(--color-primary)",
                background: "var(--bg-canvas)",
                foreground: "var(--on-canvas)",
                primary: {
                    DEFAULT: "var(--color-primary)",
                    foreground: "var(--on-primary)",
                },
                secondary: {
                    DEFAULT: "var(--bg-surface-1)",
                    foreground: "var(--on-surface)",
                },
                muted: {
                    DEFAULT: "var(--bg-subtle)",
                    foreground: "var(--on-muted)",
                },
                accent: {
                    DEFAULT: "var(--color-accent)",
                    foreground: "var(--on-accent)",
                },
                card: {
                    DEFAULT: "var(--bg-surface-1)",
                    foreground: "var(--on-surface)",
                },
                destructive: {
                    DEFAULT: "var(--color-error)",
                    foreground: "var(--on-primary)",
                },
            },
            // Accordion animations for Radix components
            keyframes: {
                "accordion-down": {
                    from: { height: 0 },
                    to: { height: "var(--radix-accordion-content-height)" },
                },
                "accordion-up": {
                    from: { height: "var(--radix-accordion-content-height)" },
                    to: { height: 0 },
                },
            },
            animation: {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
            },
        },
    },
    plugins: [],
}

