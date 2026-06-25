import { useState, useMemo, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { statusColors } from "@/lib/utils";
import { useTmdbSearch, useAnilistSearch, useAddMedia } from "@/hooks/useSearch";
import { useMediaList } from "@/hooks/useMedia";
import { useSettingsStore } from "@/store/useSettingsStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MagnifyingGlassIcon, PlusIcon } from "@heroicons/react/24/outline";
import type { ContentType, WatchStatus, SearchResult, TMDBSearchResult, AniListSearchResult } from "@/types";
import { toast } from "@/hooks/use-toast";

const CONTENT_TYPES: { label: string; value: ContentType; tmdbType: string }[] = [
  { label: "Movie", value: "MOVIE", tmdbType: "movie" },
  { label: "TV Show", value: "TV_SHOW", tmdbType: "tv" },
  { label: "Cartoon", value: "CARTOON", tmdbType: "tv" },
  { label: "Anime", value: "ANIME", tmdbType: "anime" },
];

const WATCH_STATUSES: { label: string; value: WatchStatus }[] = [
  { label: "Plan to Watch", value: "PLAN_TO_WATCH" },
  { label: "Watching", value: "WATCHING" },
  { label: "Completed", value: "COMPLETED" },
  { label: "Favorite", value: "FAVORITE" },
  { label: "Dropped", value: "DROPPED" },
];


function useDebounce(value: string, delay: number) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

export function Search() {
  const [selectedType, setSelectedType] = useState<ContentType>("MOVIE");
  const [rawQuery, setRawQuery] = useState("");
  const debouncedQuery = useDebounce(rawQuery, 500);

  const tmdbMediaType = CONTENT_TYPES.find(ct => ct.value === selectedType)?.tmdbType || "movie";
  const isAnime = selectedType === "ANIME";

  // Fetch from the appropriate API
  const tmdbSearch = useTmdbSearch(debouncedQuery, tmdbMediaType, !isAnime);
  const anilistSearch = useAnilistSearch(debouncedQuery, isAnime);

  const isSearching = isAnime ? anilistSearch.isFetching : tmdbSearch.isFetching;
  const searchError = isAnime ? anilistSearch.error : tmdbSearch.error;

  // Existing media from dashboard (for duplicate detection by title)
  const { data: existingMedia = [] } = useMediaList();
  const existingTitles = useMemo(
    () => new Map(existingMedia.map(m => [m.title.toLowerCase(), m.watch_status])),
    [existingMedia]
  );

  // Settings check for TMDB API key
  const tmdbApiKey = useSettingsStore(s => s.tmdbApiKey);
  const needsTmdbKey = !isAnime && !tmdbApiKey;

  // Normalize results into a common shape
  const results: SearchResult[] = useMemo(() => {
    if (isAnime) {
      return (anilistSearch.data || []).map((r: AniListSearchResult) => ({
        id: `anilist-${r.anilist_id}`,
        externalId: r.anilist_id,
        source: "anilist" as const,
        title: r.title,
        description: r.description,
        cover_image_url: r.cover_image_url,
        release_year: r.release_year,
        mediaType: "anime",
        episodesCount: r.episodes_count,
        genres: r.genres,
        averageScore: r.average_score,
      }));
    }
    return (tmdbSearch.data || []).map((r: TMDBSearchResult) => ({
      id: `tmdb-${r.tmdb_id}`,
      externalId: r.tmdb_id,
      source: "tmdb" as const,
      title: r.title,
      description: r.description,
      cover_image_url: r.cover_image_url,
      release_year: r.release_year,
      mediaType: r.media_type,
    }));
  }, [isAnime, anilistSearch.data, tmdbSearch.data]);

  // Add media mutation
  const { mutate: addMedia, isPending: isAdding } = useAddMedia();

  const handleAdd = useCallback((result: SearchResult, watchStatus: WatchStatus) => {
    addMedia(
      {
        content_type: selectedType,
        title: result.title,
        description: result.description,
        cover_image_url: result.cover_image_url,
        watch_status: watchStatus,
        tmdb_id: result.source === "tmdb" ? result.externalId : undefined,
      },
      {
        onSuccess: () => {
          toast({
            title: "Added!",
            description: `"${result.title}" has been added to your list.`,
          });
        },
      }
    );
  }, [addMedia, selectedType]);

  // Find existing status for a search result (match by title)
  const getExistingStatus = useCallback((result: SearchResult): WatchStatus | null => {
    const status = existingTitles.get(result.title.toLowerCase());
    return status || null;
  }, [existingTitles]);

  return (
    <div className="p-6 md:p-10 space-y-8 max-w-[1200px] mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Search & Add</h1>
        <p className="text-muted-foreground mt-1">
          Find movies, TV shows, and anime to add to your list.
        </p>
      </div>

      {/* Content Type Selector */}
      <div className="flex flex-wrap gap-2">
        {CONTENT_TYPES.map(ct => (
          <Button
            key={ct.value}
            variant={selectedType === ct.value ? "default" : "outline"}
            onClick={() => { setSelectedType(ct.value); setRawQuery(""); }}
            className="px-5"
          >
            {ct.label}
          </Button>
        ))}
      </div>

      {/* Search Input */}
      <div className="space-y-2">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <Input
            placeholder={`Search for ${CONTENT_TYPES.find(ct => ct.value === selectedType)?.label.toLowerCase()}...`}
            className="pl-10 bg-card border-border text-lg h-12"
            value={rawQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRawQuery(e.target.value)}
          />
        </div>

        {/* TMDB API key warning */}
        {needsTmdbKey && (
          <p className="text-sm text-destructive">
            TMDB API key is not configured.{" "}
            <Link to="/settings" className="underline hover:text-destructive/80">
              Go to Settings to add it
            </Link>.
          </p>
        )}
      </div>

      {/* Loading indicator */}
      {isSearching && (
        <div className="text-muted-foreground animate-pulse text-center py-8">
          Searching...
        </div>
      )}

      {/* Results */}
      {!isSearching && debouncedQuery.length >= 3 && results.length === 0 && !searchError && (
        <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-border">
          <p className="text-muted-foreground">No results found for "{debouncedQuery}"</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map(result => {
            const existingStatus = getExistingStatus(result);

            return (
              <div
                key={result.id}
                className="flex gap-4 bg-card border border-border rounded-lg p-4 hover:bg-muted/30 transition-colors"
              >
                {/* Cover */}
                <div className="w-20 h-28 rounded overflow-hidden bg-muted shrink-0">
                  {result.cover_image_url ? (
                    <img
                      src={result.cover_image_url}
                      alt={result.title}
                      className="w-full h-full object-cover"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs text-muted-foreground">
                      No image
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0 space-y-1">
                  <h3 className="font-semibold text-lg text-foreground line-clamp-1">{result.title}</h3>
                  <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                    <span>{result.release_year || "Unknown Year"}</span>
                    {result.mediaType && (
                      <>
                        <span>•</span>
                        <span className="capitalize">{result.mediaType === "tv" ? "TV Show" : result.mediaType}</span>
                      </>
                    )}
                    {result.episodesCount != null && (
                      <>
                        <span>•</span>
                        <span>{result.episodesCount} episodes</span>
                      </>
                    )}
                    {result.averageScore != null && (
                      <>
                        <span>•</span>
                        <span>Score: {result.averageScore}%</span>
                      </>
                    )}
                  </div>
                  {result.genres && result.genres.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {result.genres.slice(0, 4).map(g => (
                        <Badge key={g} variant="secondary" className="text-xs font-normal">{g}</Badge>
                      ))}
                    </div>
                  )}
                  <p className="text-sm text-muted-foreground line-clamp-2 pt-1">
                    {result.description || "No description available."}
                  </p>
                </div>

                {/* Action */}
                <div className="flex items-center shrink-0">
                  {existingStatus ? (
                    <Badge className={`${statusColors[existingStatus]} text-white border-none px-3 py-1`}>
                      {existingStatus.replace(/_/g, " ")}
                    </Badge>
                  ) : (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm" disabled={isAdding || needsTmdbKey}>
                          <PlusIcon className="w-4 h-4 mr-1" /> Add
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {WATCH_STATUSES.map(ws => (
                          <DropdownMenuItem
                            key={ws.value}
                            onClick={() => handleAdd(result, ws.value)}
                          >
                            {ws.label}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
