export type ContentType = "MOVIE" | "TV_SHOW" | "CARTOON" | "ANIME";
export type WatchStatus = "PLAN_TO_WATCH" | "WATCHING" | "COMPLETED" | "FAVORITE" | "DROPPED";

export interface Tag {
  id: string;
  name: string;
}

export interface Genre {
  id: string;
  name: string;
}

export interface Screenshot {
  id: string;
  url: string;
  sort_order: number;
}

export interface Episode {
  id: string;
  episode_number: number;
  title: string | null;
  is_watched: boolean;
  runtime_minutes: number | null;
}

export interface Season {
  id: string;
  season_number: number;
  title: string | null;
  episodes: Episode[];
}

export interface MediaBrief {
  id: string;
  content_type: ContentType;
  title: string;
  description: string | null;
  my_rating: number | null;
  watch_status: WatchStatus;
  is_rewatch: boolean;
  cover_image_url: string | null;
  local_cover_url: string | null;
  global_rating: number | null;
  release_year: number | null;
  runtime_minutes: number | null;
  created_at: string;
  updated_at: string | null;
  tags: Tag[];
  genres: Genre[];
}

export interface Media extends MediaBrief {
  web_url: string | null;
  local_network_url: string | null;
  my_comments: string | null;
  api_audio_languages: string[] | null;
  api_subtitle_languages: string[] | null;
  local_audio_languages: string[] | null;
  local_subtitle_languages: string[] | null;
  tmdb_id: number | null;
  seasons: Season[];
  screenshots: Screenshot[];
}

// ── Search result types ────────────────────────────────────────────────

export interface TMDBSearchResult {
  tmdb_id: number;
  title: string;
  description: string | null;
  cover_image_url: string | null;
  release_year: number | null;
  media_type: string; // "movie" or "tv"
}

export interface AniListSearchResult {
  anilist_id: number;
  title: string;
  description: string | null;
  cover_image_url: string | null;
  release_year: number | null;
  genres: string[];
  average_score: number | null;
  episodes_count: number | null;
}

// ── Normalized search result for UI ────────────────────────────────────

export interface SearchResult {
  id: string;            // unique key for React ("tmdb-123" or "anilist-456")
  externalId: number;    // tmdb_id or anilist_id
  source: "tmdb" | "anilist";
  title: string;
  description: string | null;
  cover_image_url: string | null;
  release_year: number | null;
  mediaType: string;     // "movie" or "tv" for tmdb; "anime" for anilist
  episodesCount?: number | null;
  genres?: string[];
  averageScore?: number | null;
}

// ── Media create payload ───────────────────────────────────────────────

export interface MediaCreatePayload {
  content_type: ContentType;
  title: string;
  description?: string | null;
  cover_image_url?: string | null;
  watch_status?: WatchStatus;
  tmdb_id?: number | null;
}
