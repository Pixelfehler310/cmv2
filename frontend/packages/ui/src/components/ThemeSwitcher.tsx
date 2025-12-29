import { useState, useEffect } from "react";
import { Moon, Sun } from "lucide-react";

export const ThemeSwitcher = () => {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window !== "undefined") {
      return document.documentElement.classList.contains("dark") ? "dark" : "light";
    }
    return "light";
  });

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  const toggleTheme = (): void => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
  };

  return (
    <button
      onClick={toggleTheme}
      className="fixed top-6 right-6 p-3 rounded-full bg-card border border-border surface-card flex items-center justify-center hover:scale-110 active:scale-95 transition-all z-50"
      aria-label="Toggle Theme"
    >
      {theme === "light" ? <Moon className="w-5 h-5 text-violet-500" /> : <Sun className="w-5 h-5 text-violet-400" />}
    </button>
  );
};
