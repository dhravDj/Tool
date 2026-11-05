import { create } from "zustand";

interface UIState {
  theme: "light" | "dark";
  isSidebarCollapsed: boolean;
  isMobileSidebarOpen: boolean;
  toggleTheme: () => void;
  setTheme: (theme: "light" | "dark") => void;
  toggleSidebar: () => void;
  setMobileSidebarOpen: (open: boolean) => void;
}

const getStoredTheme = (): "light" | "dark" => {
  if (typeof window !== "undefined" && typeof window.localStorage !== "undefined") {
    try {
      const stored = window.localStorage.getItem("documind-theme");
      if (stored === "light" || stored === "dark") return stored;
    } catch {
      // ignore fallback
    }
  }
  return "dark";
};

const persistTheme = (theme: "light" | "dark") => {
  if (typeof window !== "undefined" && typeof window.localStorage !== "undefined") {
    try {
      window.localStorage.setItem("documind-theme", theme);
    } catch {
      // ignore
    }
  }
  if (typeof document !== "undefined") {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }
};

export const useUIStore = create<UIState>((set) => {
  const initialTheme = getStoredTheme();
  if (typeof document !== "undefined") {
    if (initialTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }

  return {
    theme: initialTheme,
    isSidebarCollapsed: false,
    isMobileSidebarOpen: false,

    toggleTheme: () =>
      set((state) => {
        const nextTheme = state.theme === "dark" ? "light" : "dark";
        persistTheme(nextTheme);
        return { theme: nextTheme };
      }),

    setTheme: (theme) => {
      persistTheme(theme);
      set({ theme });
    },

    toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
    setMobileSidebarOpen: (open) => set({ isMobileSidebarOpen: open }),
  };
});
