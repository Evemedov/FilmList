import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useUploadImage() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      const { data } = await api.post<{ url: string }>("/upload/image", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return data.url;
    },
  });
}
