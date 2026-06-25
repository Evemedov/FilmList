import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { TMDBSearchResult, AniListSearchResult, MediaCreatePayload, Media } from "@/types";

export function useTmdbSearch(query: string, mediaType: string, enabled: boolean) {
  return useQuery({
    queryKey: ["tmdb-search", query, mediaType],
    queryFn: async () => {
      const { data } = await api.get<TMDBSearchResult[]>("/tmdb/search", {
        params: { q: query, media_type: mediaType },
      });
      return data;
    },
    enabled: enabled && query.length >= 3,
    staleTime: 1000 * 60 * 5, // 5 min client cache
  });
}

export function useAnilistSearch(query: string, enabled: boolean) {
  return useQuery({
    queryKey: ["anilist-search", query],
    queryFn: async () => {
      const { data } = await api.get<AniListSearchResult[]>("/anilist/search", {
        params: { q: query },
      });
      return data;
    },
    enabled: enabled && query.length >= 3,
    staleTime: 1000 * 60 * 5,
  });
}

export function useAddMedia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: MediaCreatePayload) => {
      const { data } = await api.post<Media>("/media", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["media"] });
    },
  });
}
