import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMediaDetail, useUpdateMedia, useUpdateEpisode } from "@/hooks/useMedia";
import { useUploadImage } from "@/hooks/useUpload";
import { toast } from "@/hooks/use-toast";
import { RatingStars } from "@/components/media/RatingStars";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ArrowLeftIcon, CheckCircleIcon, PencilSquareIcon, PhotoIcon } from "@heroicons/react/24/outline";
import { StarIcon } from "@heroicons/react/24/solid";
import { statusColors } from "@/lib/utils";
import type { Media, WatchStatus } from "@/types";

export function MediaDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: media, isLoading, error } = useMediaDetail(id!);
  const { mutate: updateMedia, isPending: isUpdating } = useUpdateMedia();
  const { mutate: updateEpisode } = useUpdateEpisode();
  const { mutate: uploadImage, isPending: isUploading } = useUploadImage();

  const [isEditMode, setIsEditMode] = useState(false);
  const [editForm, setEditForm] = useState<Partial<Media>>({});
  const [activeSeason, setActiveSeason] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (media && !activeSeason && media.seasons.length > 0) {
      setActiveSeason(media.seasons[0].id);
    }
  }, [media, activeSeason]);

  const handleEditToggle = () => {
    if (isEditMode) {
      // Validate URLs
      const isValidUrl = (url: string) => {
        try {
          new URL(url);
          return true;
        } catch {
          return false;
        }
      };

      if (editForm.web_url && !isValidUrl(editForm.web_url)) {
        toast({ title: "Invalid URL", description: "Web URL is not a valid URL.", variant: "destructive" });
        return;
      }
      if (editForm.local_network_url && !isValidUrl(editForm.local_network_url)) {
        toast({ title: "Invalid URL", description: "Local Network URL is not a valid URL.", variant: "destructive" });
        return;
      }
      if (editForm.local_cover_url && !isValidUrl(editForm.local_cover_url) && !editForm.local_cover_url.startsWith("/")) {
        toast({ title: "Invalid URL", description: "Local Cover URL is not a valid URL.", variant: "destructive" });
        return;
      }

      // Save
      updateMedia(
        { id: media!.id, data: editForm },
        {
          onSuccess: () => setIsEditMode(false),
        }
      );
    } else {
      // Enter edit mode
      setEditForm({
        my_rating: media!.my_rating,
        my_comments: media!.my_comments,
        watch_status: media!.watch_status,
        local_cover_url: media!.local_cover_url,
        web_url: media!.web_url,
        local_network_url: media!.local_network_url,
      });
      setIsEditMode(true);
    }
  };

  if (isLoading) return <div className="p-10 animate-pulse text-muted-foreground">Loading...</div>;
  if (error || !media) return <div className="p-10 text-destructive">Failed to load media.</div>;

  const coverUrl = isEditMode
    ? (editForm.local_cover_url || media.cover_image_url || "/placeholder-cover.jpg")
    : (media.local_cover_url || media.cover_image_url || "/placeholder-cover.jpg");

  return (
    <div className="p-6 md:p-10 space-y-8 max-w-[1200px] mx-auto pb-20">
      <Button variant="ghost" onClick={() => navigate(-1)} className="-ml-4 text-muted-foreground hover:text-foreground">
        <ArrowLeftIcon className="w-4 h-4 mr-2" /> Back
      </Button>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Sidebar / Poster */}
        <div className="w-full md:w-1/3 lg:w-1/4 space-y-4">
          <div className="aspect-[2/3] w-full rounded-lg overflow-hidden border border-border bg-muted relative">
            <img 
              src={coverUrl || "/placeholder-cover.jpg"} 
              alt={media.title} 
              className="w-full h-full object-cover"
              onError={(e) => { (e.target as HTMLImageElement).src = "/placeholder-cover.jpg"; }}
            />
          </div>

          {isEditMode ? (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted-foreground">Local Cover URL</label>
              <div className="flex gap-2">
                <Input 
                  value={editForm.local_cover_url || ""} 
                  onChange={(e) => setEditForm(prev => ({ ...prev, local_cover_url: e.target.value }))}
                  placeholder="https://..."
                />
                <Button 
                  variant="secondary" 
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="px-3"
                  title="Upload Cover"
                >
                  <PhotoIcon className="w-5 h-5" />
                </Button>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  className="hidden" 
                  accept="image/*"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      uploadImage(file, {
                        onSuccess: (url) => setEditForm(prev => ({ ...prev, local_cover_url: url }))
                      });
                    }
                  }}
                />
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full"
                onClick={() => setEditForm(prev => ({ ...prev, local_cover_url: null }))}
              >
                Remove Local Cover
              </Button>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {media.web_url && (
                <a href={media.web_url} target="_blank" rel="noreferrer" className="w-full">
                  <Button variant="outline" className="w-full bg-card">Watch Online</Button>
                </a>
              )}
              {media.local_network_url && (
                <a href={media.local_network_url} target="_blank" rel="noreferrer" className="w-full">
                  <Button variant="secondary" className="w-full">Open Local File</Button>
                </a>
              )}
              
              <div className="mt-4 space-y-4 p-4 bg-card border border-border rounded-lg text-sm">
                <div className="space-y-1">
                  <span className="text-muted-foreground block text-xs font-semibold uppercase tracking-wider">Added to List</span>
                  <div>{new Date(media.created_at).toLocaleDateString()}</div>
                </div>

                {media.global_rating !== null && (
                  <div className="space-y-1">
                    <span className="text-muted-foreground block text-xs font-semibold uppercase tracking-wider">TMDB Rating</span>
                    <div className="flex items-center space-x-1 text-yellow-500">
                      <StarIcon className="w-4 h-4" />
                      <span className="font-medium text-foreground">{(media.global_rating / 2).toFixed(1)}</span>
                    </div>
                  </div>
                )}

                {media.runtime_minutes && (
                  <div className="space-y-1">
                    <span className="text-muted-foreground block text-xs font-semibold uppercase tracking-wider">Runtime</span>
                    <div>{media.runtime_minutes} minutes</div>
                  </div>
                )}

                {(media.api_audio_languages?.length || 0) > 0 && (
                  <div className="space-y-1">
                    <span className="text-muted-foreground block text-xs font-semibold uppercase tracking-wider">Audio</span>
                    <div className="flex flex-wrap gap-1">
                      {media.api_audio_languages!.map(lang => (
                        <Badge key={lang} variant="secondary" className="text-[10px] px-1 py-0">{lang.toUpperCase()}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {(media.api_subtitle_languages?.length || 0) > 0 && (
                  <div className="space-y-1">
                    <span className="text-muted-foreground block text-xs font-semibold uppercase tracking-wider">Subtitles</span>
                    <div className="flex flex-wrap gap-1">
                      {media.api_subtitle_languages!.map(lang => (
                        <Badge key={lang} variant="outline" className="text-[10px] px-1 py-0">{lang.toUpperCase()}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="flex-1 space-y-6">
          <div className="flex justify-between items-start gap-4">
            <div>
              <h1 className="text-4xl font-bold tracking-tight">{media.title}</h1>
              <div className="flex flex-wrap items-center gap-2 mt-2 text-sm text-muted-foreground">
                <span>{media.release_year || "Unknown Year"}</span>
                <span>•</span>
                <span className="capitalize">{media.content_type.toLowerCase().replace("_", " ")}</span>
                {media.runtime_minutes && (
                  <>
                    <span>•</span>
                    <span>{media.runtime_minutes} min</span>
                  </>
                )}
              </div>
            </div>
            <Button 
              variant={isEditMode ? "default" : "secondary"}
              onClick={handleEditToggle}
              disabled={isUpdating}
            >
              {isEditMode ? (
                <>Save Changes</>
              ) : (
                <><PencilSquareIcon className="w-4 h-4 mr-2" /> Edit</>
              )}
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {isEditMode ? (
              <select 
                className="bg-card border border-border rounded-md px-3 py-1 text-sm"
                value={editForm.watch_status || media.watch_status}
                onChange={(e) => setEditForm(prev => ({ ...prev, watch_status: e.target.value as WatchStatus }))}
              >
                <option value="PLAN_TO_WATCH">Plan to Watch</option>
                <option value="WATCHING">Watching</option>
                <option value="COMPLETED">Completed</option>
                <option value="FAVORITE">Favorite</option>
                <option value="DROPPED">Dropped</option>
              </select>
            ) : (
              <Badge className={`${statusColors[media.watch_status] || "bg-slate-500"} text-white border-none shadow-md`}>
                {media.watch_status.replace(/_/g, " ")}
              </Badge>
            )}
            
            {media.genres.map(g => (
              <Badge key={g.id} variant="secondary" className="font-normal">{g.name}</Badge>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-card border border-border p-6 rounded-lg">
            <div className="space-y-4">
              <h3 className="font-semibold text-lg border-b border-border pb-2">My Rating</h3>
              <RatingStars 
                rating={isEditMode ? editForm.my_rating! : media.my_rating} 
                readOnly={!isEditMode}
                onChange={(val) => setEditForm(prev => ({ ...prev, my_rating: val }))}
              />
              
              {isEditMode && (
                <>
                  <div className="pt-4 space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground">Web URL</label>
                    <Input 
                      type="url"
                      value={editForm.web_url || ""} 
                      onChange={(e) => setEditForm(prev => ({ ...prev, web_url: e.target.value }))}
                      placeholder="https://..."
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground">Local Filebrowser URL</label>
                    <Input 
                      type="url"
                      value={editForm.local_network_url || ""} 
                      onChange={(e) => setEditForm(prev => ({ ...prev, local_network_url: e.target.value }))}
                      placeholder="http://192.168..."
                    />
                  </div>
                </>
              )}
            </div>
            
            <div className="space-y-2">
              <h3 className="font-semibold text-lg border-b border-border pb-2">Comments</h3>
              {isEditMode ? (
                <textarea 
                  value={editForm.my_comments || ""} 
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditForm(prev => ({ ...prev, my_comments: e.target.value }))}
                  placeholder="Write your thoughts here..."
                  className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              ) : (
                <p className="text-muted-foreground text-sm leading-relaxed whitespace-pre-wrap">
                  {media.my_comments || "No comments yet."}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="font-semibold text-lg">Synopsis</h3>
            <p className="text-muted-foreground leading-relaxed">
              {media.description || "No description available."}
            </p>
          </div>

          {/* TV/Anime Episodic UI */}
          {media.seasons.length > 0 && (
            <div className="pt-8 space-y-4">
              <h3 className="font-semibold text-2xl tracking-tight border-b border-border pb-2">Seasons</h3>
              
              <div className="flex overflow-x-auto space-x-2 pb-2">
                {media.seasons.map(season => (
                  <Button
                    key={season.id}
                    variant={activeSeason === season.id ? "default" : "outline"}
                    onClick={() => setActiveSeason(season.id)}
                    className="shrink-0"
                  >
                    Season {season.season_number}
                  </Button>
                ))}
              </div>

              <div className="bg-card border border-border rounded-lg overflow-hidden">
                {media.seasons.find(s => s.id === activeSeason)?.episodes.map((ep) => (
                  <div key={ep.id} className="flex items-center justify-between p-4 border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">
                        Episode {ep.episode_number}
                      </span>
                      {ep.title && (
                        <span className="text-sm text-muted-foreground">{ep.title}</span>
                      )}
                    </div>
                    <Button
                      variant={ep.is_watched ? "default" : "outline"}
                      size="sm"
                      onClick={() => updateEpisode({ mediaId: media.id, episodeId: ep.id, isWatched: !ep.is_watched })}
                      className={ep.is_watched ? "bg-green-600 hover:bg-green-700 text-white" : "bg-card text-muted-foreground"}
                    >
                      <CheckCircleIcon className="w-4 h-4 mr-2" />
                      {ep.is_watched ? "Watched" : "Unwatched"}
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
