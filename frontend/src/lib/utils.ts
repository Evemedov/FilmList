import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const statusColors: Record<string, string> = {
  PLAN_TO_WATCH: "bg-slate-500",
  WATCHING: "bg-blue-500",
  COMPLETED: "bg-green-500",
  FAVORITE: "bg-purple-500",
  DROPPED: "bg-red-500",
};
