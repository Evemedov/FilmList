import { useState, useMemo } from "react";
import { useMediaList } from "@/hooks/useMedia";
import { MediaGrid } from "@/components/media/MediaGrid";
import { MediaTable } from "@/components/media/MediaTable";
import { MediaFilters, type FilterState } from "@/components/media/MediaFilters";
import { Squares2X2Icon, ListBulletIcon, MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

type ViewMode = "grid" | "table";

export function Dashboard() {
  const { data: mediaItems = [], isLoading, error } = useMediaList();
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<FilterState>({
    status: null,
    type: null,
    hasLocalFile: null,
    minRating: null,
  });

  const filteredMedia = useMemo(() => {
    let result = mediaItems;
    
    // Apply text search
    if (searchQuery.trim()) {
      const lowerQuery = searchQuery.toLowerCase();
      result = result.filter(item => 
        item.title.toLowerCase().includes(lowerQuery)
      );
    }
    
    // Apply advanced filters
    if (filters.status) {
      result = result.filter(item => item.watch_status === filters.status);
    }
    if (filters.type) {
      result = result.filter(item => item.content_type === filters.type);
    }
    if (filters.hasLocalFile) {
      result = result.filter(item => !!(item as any).local_network_url || !!item.local_cover_url);
    }
    
    return result;
  }, [mediaItems, searchQuery, filters]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-muted-foreground animate-pulse">Loading media...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-destructive">Failed to load media. Is the backend running?</div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-10 space-y-8 max-w-[1600px] mx-auto">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">My film list</h1>
          <p className="text-muted-foreground mt-1">
            Track your movies, TV shows, and anime.
          </p>
        </div>
        
        <div className="flex items-center space-x-2 bg-card p-1 rounded-md border border-border">
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setViewMode("grid")}
            className="px-2"
          >
            <Squares2X2Icon className="h-5 w-5" />
          </Button>
          <Button
            variant={viewMode === "table" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setViewMode("table")}
            className="px-2"
          >
            <ListBulletIcon className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Basic Search and Filters Placeholder */}
      <div className="bg-card border border-border rounded-lg p-4 flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <Input 
            placeholder="Search media by title..." 
            className="pl-10 bg-background"
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex space-x-2">
          <MediaFilters filters={filters} setFilters={setFilters} />
        </div>
      </div>

      {/* Content View */}
      {viewMode === "grid" ? (
        <MediaGrid items={filteredMedia} />
      ) : (
        <MediaTable items={filteredMedia} />
      )}
    </div>
  );
}
