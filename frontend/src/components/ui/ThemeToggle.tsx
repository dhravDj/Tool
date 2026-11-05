import React from "react";
import { Moon, Sun } from "lucide-react";
import { useUIStore } from "@/stores/uiStore";

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useUIStore();

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
      aria-label="Toggle theme"
      title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
    >
      {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
};
