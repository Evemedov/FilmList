import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { MediaBrief, Media } from "@/types";

export function useMediaList() {
  return useQuery({
    queryKey: ["media"],
    queryFn: async () => {
      const { data } = await api.get<MediaBrief[]>("/media");
      return data;
    },
  });
}

export function useMediaDetail(id: string) {
  return useQuery({
    queryKey: ["media", id],
    queryFn: async () => {
      const { data } = await api.get<Media>(`/media/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useUpdateMedia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Media> }) => {
      const res = await api.patch<Media>(`/media/${id}`, data);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["media", data.id], data);
      queryClient.invalidateQueries({ queryKey: ["media"] });
    },
  });
}

export function useUpdateEpisode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ mediaId, episodeId, isWatched }: { mediaId: string; episodeId: string; isWatched: boolean }) => {
      const res = await api.patch(`/media/${mediaId}/episodes/${episodeId}`, { is_watched: isWatched });
      return res.data;
    },
    onSuccess: (_, variables) => {
      // Invalidate the specific media to trigger a refetch and get updated cascading status
      queryClient.invalidateQueries({ queryKey: ["media", variables.mediaId] });
    },
  });
}
