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
            colors: {
                border: "var(--border-subtle)",
                input: "var(--bg-input)",
                ring: "var(--accent-main)",
                background: "var(--bg-app)",
                foreground: "var(--text-primary)",
                primary: {
                    DEFAULT: "var(--accent-main)",
                    foreground: "white",
                },
                secondary: {
                    DEFAULT: "var(--bg-section)",
                    foreground: "var(--text-primary)",
                },
                muted: {
                    DEFAULT: "var(--bg-section)",
                    foreground: "var(--text-muted)",
                },
                accent: {
                    DEFAULT: "var(--accent-main)",
                    foreground: "white",
                },
                card: {
                    DEFAULT: "var(--bg-panel)",
                    foreground: "var(--text-primary)",
                },
            },
            fontFamily: {
                sans: ["'Plus Jakarta Sans'", "system-ui", "-apple-system", "sans-serif"],
            },
            borderRadius: {
                "3xl": "24px",
                "2xl": "16px",
                xl: "12px",
                lg: "var(--radius)",
                md: "calc(var(--radius) - 8px)",
                sm: "calc(var(--radius) - 16px)",
            },
            keyframes: {
                boing: {
                    "0%": { transform: "scale(1)" },
                    "40%": { transform: "scale(0.92)" },
                    "70%": { transform: "scale(1.05)" },
                    "100%": { transform: "scale(1)" },
                },
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
                boing: "boing 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
            },
        },
    },
    plugins: [],
}
