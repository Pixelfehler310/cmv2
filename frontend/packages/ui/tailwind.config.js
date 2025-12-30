import civicTheme from "@civic/design-system/tailwind";

/** @type {import('tailwindcss').Config} */
export default {
    presets: [civicTheme],
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
                input: "var(--bg-input)",
                ring: "var(--color-primary)",
                background: "var(--bg-canvas)",
                foreground: "var(--text-primary)",
                primary: {
                    DEFAULT: "var(--color-primary)",
                    foreground: "white",
                },
                secondary: {
                    DEFAULT: "var(--bg-surface)",
                    foreground: "var(--text-primary)",
                },
                muted: {
                    DEFAULT: "var(--bg-subtle)",
                    foreground: "var(--text-muted)",
                },
                accent: {
                    DEFAULT: "var(--color-accent)",
                    foreground: "white",
                },
                card: {
                    DEFAULT: "var(--bg-surface)",
                    foreground: "var(--text-primary)",
                },
                destructive: {
                    DEFAULT: "var(--color-alert-500)",
                    foreground: "white",
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
