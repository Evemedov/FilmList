import { StarIcon as StarSolid } from "@heroicons/react/24/solid";
import { StarIcon as StarOutline } from "@heroicons/react/24/outline";

interface RatingStarsProps {
  rating: number | null; // 1 to 10
  onChange?: (rating: number) => void;
  readOnly?: boolean;
}

export function RatingStars({ rating, onChange, readOnly = false }: RatingStarsProps) {
  // We represent 1-10 rating as 5 stars with half stars, but for interactive mode
  // we can just make it click on 10 half-star hitboxes, or just 5 full stars.
  // The requirement says: "rendered visually as 5 stars with half-star increments".
  // For simplicity in Edit Mode, we can use 5 stars and allow clicking left/right half.
  
  const currentRating = rating || 0;

  const handleStarClick = (index: number, isHalf: boolean) => {
    if (readOnly || !onChange) return;
    const newRating = (index * 2) + (isHalf ? 1 : 2);
    onChange(newRating);
  };

  return (
    <div className="flex items-center space-x-1">
      {[...Array(5)].map((_, i) => {
        const starValue = (i + 1) * 2;
        const isFull = currentRating >= starValue;
        const isHalf = currentRating === starValue - 1;

        return (
          <div key={i} className={`relative ${readOnly ? "" : "cursor-pointer"} w-6 h-6`}>
            {/* Outline background */}
            <StarOutline className="absolute top-0 left-0 w-6 h-6 text-muted-foreground" />
            
            {/* Full Star */}
            {isFull && (
              <StarSolid className="absolute top-0 left-0 w-6 h-6 text-yellow-500" />
            )}
            
            {/* Half Star (using clipping) */}
            {isHalf && (
              <div className="absolute top-0 left-0 overflow-hidden w-3 h-6">
                <StarSolid className="w-6 h-6 text-yellow-500" />
              </div>
            )}

            {/* Click handlers for half/full */}
            {!readOnly && (
              <div className="absolute top-0 left-0 w-full h-full flex">
                <div className="w-1/2 h-full" onClick={() => handleStarClick(i, true)} />
                <div className="w-1/2 h-full" onClick={() => handleStarClick(i, false)} />
              </div>
            )}
          </div>
        );
      })}
      <span className="ml-2 text-sm text-muted-foreground">
        {currentRating > 0 ? (currentRating / 2).toFixed(1) : "Unrated"}
      </span>
    </div>
  );
}
