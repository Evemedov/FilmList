import type { MediaBrief } from "@/types";
import { Link } from "react-router-dom";
import { StarIcon } from "@heroicons/react/24/solid";
import { Badge } from "@/components/ui/badge";
import { statusColors } from "@/lib/utils";


export function MediaTable({ items }: { items: MediaBrief[] }) {
  if (items.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-border">
        <p className="text-muted-foreground">No media found.</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-border overflow-x-auto bg-card">
      <table className="w-full text-sm text-left">
        <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b border-border">
          <tr>
            <th className="px-6 py-3">Title</th>
            <th className="px-6 py-3">Type</th>
            <th className="px-6 py-3">Year</th>
            <th className="px-6 py-3">Rating</th>
            <th className="px-6 py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((media) => (
            <tr key={media.id} className="border-b border-border hover:bg-muted/30 transition-colors">
              <td className="px-6 py-4 font-medium text-foreground">
                <Link to={`/media/${media.id}`} className="hover:underline hover:text-primary">
                  {media.title}
                </Link>
              </td>
              <td className="px-6 py-4 capitalize text-muted-foreground">
                {media.content_type.toLowerCase().replace("_", " ")}
              </td>
              <td className="px-6 py-4 text-muted-foreground">
                {media.release_year || "-"}
              </td>
              <td className="px-6 py-4">
                <div className="flex items-center text-yellow-500 space-x-1">
                  <StarIcon className="w-4 h-4" />
                  <span className="text-foreground">
                    {media.my_rating ? (media.my_rating / 2).toFixed(1) : "-"}
                  </span>
                </div>
              </td>
              <td className="px-6 py-4">
                <Badge className={`${statusColors[media.watch_status] || "bg-slate-500"} text-white border-none`}>
                  {media.watch_status.replace(/_/g, ' ')}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
