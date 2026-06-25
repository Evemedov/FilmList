import { NavLink } from "react-router-dom";
import {
  HomeIcon,
  FilmIcon,
  Cog6ToothIcon,
  MagnifyingGlassIcon
} from "@heroicons/react/24/outline";
import { cn } from "@/lib/utils";
import { SiGithub } from "react-icons/si";

const navigation = [
  { name: "Dashboard", href: "/", icon: HomeIcon },
  { name: "Search & Add", href: "/search", icon: MagnifyingGlassIcon },
  { name: "Settings", href: "/settings", icon: Cog6ToothIcon },
];

export function Sidebar() {
  return (
    <div className="flex h-full w-64 flex-col bg-card border-r border-border">
      <div className="flex h-16 items-center px-6">
        <NavLink to="/" className="flex items-center gap-2 font-bold text-xl tracking-tight text-foreground hover:opacity-80 transition-opacity">
          <FilmIcon className="h-6 w-6 text-primary" />
          <span>FilmList</span>
        </NavLink>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        <div className="mb-4 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          General
        </div>
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                "group flex items-center rounded-md px-3 py-2 text-sm font-medium",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )
            }
          >
            <item.icon
              className="mr-3 h-5 w-5 flex-shrink-0"
              aria-hidden="true"
            />
            {item.name}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-border flex flex-col items-center gap-1">
        <p className="text-xs text-muted-foreground">
          Created by Evemed
        </p>
        <a
          href="https://github.com/Evemedov/FilmList"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-primary hover:underline transition-colors duration-200"
        >
          <SiGithub className="h-3.5 w-3.5" />
          <span>GitHub</span>
        </a>
      </div>
    </div>
  );
}
