import { useState, useEffect } from "react";
import { useSettingsStore } from "@/store/useSettingsStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/hooks/use-toast";
import { MoonIcon, SunIcon, KeyIcon } from "@heroicons/react/24/outline";

export function Settings() {
  const { theme, setTheme, tmdbApiKey, setTmdbApiKey } = useSettingsStore();
  const [apiKeyInput, setApiKeyInput] = useState("");

  useEffect(() => {
    if (tmdbApiKey) {
      setApiKeyInput(tmdbApiKey);
    }
  }, [tmdbApiKey]);

  const handleSaveApiKey = () => {
    setTmdbApiKey(apiKeyInput || null);
    toast({
      title: "Success",
      description: "TMDB API Key saved successfully.",
    });
  };

  return (
    <div className="p-6 md:p-10 space-y-8 max-w-[800px] mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your application preferences and API keys.
        </p>
      </div>

      <div className="grid gap-6">
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {theme === "DARK" ? <MoonIcon className="w-5 h-5" /> : <SunIcon className="w-5 h-5" />}
              Appearance
            </CardTitle>
            <CardDescription>
              Customize the look and feel of the application.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <Button
                variant={theme === "LIGHT" ? "default" : "outline"}
                onClick={() => setTheme("LIGHT")}
                className="w-32"
              >
                <SunIcon className="w-4 h-4 mr-2" /> Light
              </Button>
              <Button
                variant={theme === "DARK" ? "default" : "outline"}
                onClick={() => setTheme("DARK")}
                className="w-32"
              >
                <MoonIcon className="w-4 h-4 mr-2" /> Dark
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KeyIcon className="w-5 h-5" />
              TMDB API Key
            </CardTitle>
            <CardDescription>
              Required for fetching metadata (posters, genres, episodes) when adding new media.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-foreground">API Key</label>
              <div className="flex gap-2">
                <Input
                  type="password"
                  placeholder="Enter your v3 API key..."
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  className="bg-background max-w-md font-mono"
                />
                <Button onClick={handleSaveApiKey}>Save</Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Your key is stored securely in the database and synced across your devices.
                Don't have one? <a href="https://developer.themoviedb.org/docs/getting-started" target="_blank" rel="noreferrer" className="text-primary hover:underline">Get your TMDB API key here&#x2197;</a>.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
