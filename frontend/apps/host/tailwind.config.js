/** @type {import('tailwindcss').Config} */
import sharedConfig from "@rpg/ui/tailwind.config.js"

export default {
    ...sharedConfig,
    content: [
        "./src/**/*.{ts,tsx}",
        "../../packages/ui/src/**/*.{ts,tsx}"
    ],
}
