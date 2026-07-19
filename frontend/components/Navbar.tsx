import Link from "next/link";
import SearchBar from "./SearchBar";

export default function Navbar() {
  return (
    <header className="border-b border-black/10 dark:border-white/10 bg-white dark:bg-black sticky top-0 z-20">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-6">
        <Link href="/" className="font-bold text-lg tracking-tight whitespace-nowrap">
          ⚽ FootballStats
        </Link>
        <nav className="hidden sm:flex gap-4 text-sm text-zinc-600 dark:text-zinc-400">
          <Link href="/leagues/en.1" className="hover:text-black dark:hover:text-white">Ligues</Link>
          <Link href="/competitions" className="hover:text-black dark:hover:text-white">Compétitions</Link>
          <Link href="/compare" className="hover:text-black dark:hover:text-white">Comparer</Link>
        </nav>
        <div className="flex-1" />
        <SearchBar />
      </div>
    </header>
  );
}
