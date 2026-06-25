import type { MediaBrief } from "@/types";
import { MediaCard } from "./MediaCard";

export function MediaGrid({ items }: { items: MediaBrief[] }) {
  if (items.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-border">
        <p className="text-muted-foreground">No media found.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
      {items.map((media) => (
        <MediaCard key={media.id} media={media} />
      ))}
    </div>
  );
}
