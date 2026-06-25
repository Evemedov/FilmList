import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "@/lib/api";

type Theme = "DARK" | "LIGHT";

interface SettingsState {
  theme: Theme;
  tmdbApiKey: string | null;
  setTheme: (theme: Theme) => void;
  setTmdbApiKey: (key: string | null) => void;
  syncWithBackend: () => Promise<void>;
  updateBackend: (theme: Theme, apiKey: string | null) => Promise<void>;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      theme: "DARK",
      tmdbApiKey: null,
      
      setTheme: (theme) => {
        set({ theme });
        document.documentElement.classList.toggle("dark", theme === "DARK");
        get().updateBackend(theme, get().tmdbApiKey);
      },
      
      setTmdbApiKey: (key) => {
        set({ tmdbApiKey: key });
        get().updateBackend(get().theme, key);
      },
      
      syncWithBackend: async () => {
        try {
          const res = await api.get("/settings");
          const { theme, tmdb_api_key } = res.data;
          set({ theme, tmdbApiKey: tmdb_api_key });
          document.documentElement.classList.toggle("dark", theme === "DARK");
        } catch (error) {
          console.error("Failed to sync settings from backend", error);
        }
      },
      
      updateBackend: async (theme, apiKey) => {
        try {
          await api.patch("/settings", {
            theme,
            tmdb_api_key: apiKey,
          });
        } catch (error) {
          console.error("Failed to update backend settings", error);
        }
      },
    }),
    {
      name: "filmlist-settings",
      onRehydrateStorage: () => (state) => {
        if (state) {
          document.documentElement.classList.toggle("dark", state.theme === "DARK");
        }
      },
    }
  )
);
