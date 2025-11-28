/** @type {import('tailwindcss').Config} */
module.exports = {
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
                border: "hsl(var(--border-subtle))",
                input: "hsl(var(--bg-panel))",
                ring: "hsl(var(--accent-main))",
                background: "hsl(var(--bg-app))",
                foreground: "hsl(var(--text-primary))",
                primary: {
                    DEFAULT: "hsl(var(--accent-main))",
                    foreground: "hsl(var(--bg-app))",
                },
                secondary: {
                    DEFAULT: "hsl(var(--palette-steel))",
                    foreground: "hsl(var(--bg-app))",
                },
                destructive: {
                    DEFAULT: "hsl(var(--palette-crimson))",
                    foreground: "hsl(var(--text-primary))",
                },
                muted: {
                    DEFAULT: "hsl(var(--bg-panel))",
                    foreground: "hsl(var(--text-muted))",
                },
                accent: {
                    DEFAULT: "hsl(var(--accent-main))",
                    foreground: "hsl(var(--bg-app))",
                },
                popover: {
                    DEFAULT: "hsl(var(--bg-panel))",
                    foreground: "hsl(var(--text-primary))",
                },
                card: {
                    DEFAULT: "hsl(var(--bg-panel))",
                    foreground: "hsl(var(--text-primary))",
                },
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
            },
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
    plugins: [require("tailwindcss-animate")],
}
