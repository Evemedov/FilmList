import type { MediaBrief } from "@/types";
import { Link } from "react-router-dom";
import { StarIcon } from "@heroicons/react/24/solid";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { statusColors } from "@/lib/utils";


export function MediaCard({ media }: { media: MediaBrief }) {
  const coverUrl = media.local_cover_url || media.cover_image_url || "/placeholder-cover.jpg";

  return (
    <Link to={`/media/${media.id}`}>
      <Card className="overflow-hidden hover:ring-2 hover:ring-primary transition-all duration-300 h-full flex flex-col bg-card border-border group cursor-pointer relative">
        <div className="relative aspect-[2/3] w-full overflow-hidden bg-muted">
          {coverUrl && (
            <img
              src={coverUrl}
              alt={media.title}
              className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500"
              onError={(e) => {
                (e.target as HTMLImageElement).src = "/placeholder-cover.jpg";
              }}
            />
          )}
          <div className="absolute top-2 right-2">
            <Badge className={`${statusColors[media.watch_status] || "bg-slate-500"} text-white border-none shadow-md`}>
              {media.watch_status.replace(/_/g, ' ')}
            </Badge>
          </div>
        </div>
        <CardContent className="p-4 flex-1 flex flex-col justify-between space-y-2">
          <div>
            <h3 className="font-semibold text-lg line-clamp-1" title={media.title}>
              {media.title}
            </h3>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground mt-1">
              <span>{media.release_year || "Unknown Year"}</span>
              <span>•</span>
              <span className="capitalize">{media.content_type.toLowerCase().replace("_", " ")}</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center text-yellow-500 space-x-1">
              <StarIcon className="w-4 h-4" />
              <span className="text-sm font-medium text-foreground">
                {media.my_rating ? (media.my_rating / 2).toFixed(1) : "Unrated"}
              </span>
            </div>
            {media.global_rating && (
              <div className="text-xs text-muted-foreground">
                TMDB: {(media.global_rating / 2).toFixed(1)}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
