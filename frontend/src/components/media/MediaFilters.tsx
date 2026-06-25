import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem
} from "@/components/ui/dropdown-menu";
import { FunnelIcon } from "@heroicons/react/24/outline";

export interface FilterState {
  status: string | null;
  type: string | null;
  hasLocalFile: boolean | null;
  minRating: number | null;
}

interface MediaFiltersProps {
  filters: FilterState;
  setFilters: React.Dispatch<React.SetStateAction<FilterState>>;
}

export function MediaFilters({ filters, setFilters }: MediaFiltersProps) {
  const handleStatusChange = (val: string) => {
    setFilters(prev => ({ ...prev, status: val === "all" ? null : val }));
  };

  const handleTypeChange = (val: string) => {
    setFilters(prev => ({ ...prev, type: val === "all" ? null : val }));
  };

  const activeFilterCount = Object.values(filters).filter(v => v !== null).length;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="bg-background relative">
          <FunnelIcon className="h-4 w-4 mr-2" />
          Filters
          {activeFilterCount > 0 && (
            <span className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
              {activeFilterCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end">
        <DropdownMenuLabel>Watch Status</DropdownMenuLabel>
        <DropdownMenuRadioGroup value={filters.status || "all"} onValueChange={handleStatusChange}>
          <DropdownMenuRadioItem value="all">All</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="PLAN_TO_WATCH">Plan to Watch</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="WATCHING">Watching</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="COMPLETED">Completed</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="FAVORITE">Favorite</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="DROPPED">Dropped</DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>
        
        <DropdownMenuSeparator />
        
        <DropdownMenuLabel>Content Type</DropdownMenuLabel>
        <DropdownMenuRadioGroup value={filters.type || "all"} onValueChange={handleTypeChange}>
          <DropdownMenuRadioItem value="all">All</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="MOVIE">Movie</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="TV_SHOW">TV Show</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="ANIME">Anime</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="CARTOON">Cartoon</DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>

        <DropdownMenuSeparator />

        <DropdownMenuCheckboxItem 
          checked={filters.hasLocalFile === true}
          onCheckedChange={(c) => setFilters(prev => ({ ...prev, hasLocalFile: c ? true : null }))}
        >
          Has Local File
        </DropdownMenuCheckboxItem>

        <DropdownMenuSeparator />
        
        <Button 
          variant="ghost" 
          className="w-full justify-center mt-2 text-xs h-8"
          onClick={() => setFilters({ status: null, type: null, hasLocalFile: null, minRating: null })}
        >
          Clear Filters
        </Button>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
