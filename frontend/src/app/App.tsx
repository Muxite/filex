import { ThemeProvider } from "next-themes";
import { useState } from "react";
import { Search, FolderOpen } from "lucide-react";
import { Input } from "@/app/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select";
import { IndexingProgress } from "@/app/components/IndexingProgress";
import { FileTypeDistribution } from "@/app/components/FileTypeDistribution";
import { DirectorySizes } from "@/app/components/DirectorySizes";
import { IndexingActivity } from "@/app/components/IndexingActivity";
import { StorageOverview } from "@/app/components/StorageOverview";
import { ThemeToggle } from "@/app/components/ThemeToggle";
import { useDirectories, useDirectoryStats } from "@/app/hooks/useDirectoryData";

function AppContent() {
  const { directories, loading: directoriesLoading } = useDirectories();
  const [selectedDirectory, setSelectedDirectory] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  // Set initial directory when directories load
  if (!selectedDirectory && directories.length > 0 && !directoriesLoading) {
    setSelectedDirectory(directories[0]);
  }

  const { stats, loading: statsLoading } = useDirectoryStats(selectedDirectory);

  if (directoriesLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading directories...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border sticky top-0 z-10 shadow-sm">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between gap-6">
            {/* Logo/Title - FILEX with wide styling */}
            <div className="flex items-center gap-3">
              <div className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-md">
                <div className="flex items-center gap-1">
                  <FolderOpen className="w-5 h-5 text-white" />
                  <h1 className="text-xl font-bold tracking-[0.3em] text-white">FILEX</h1>
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Semantic File System Search</p>
              </div>
            </div>

            {/* Search and Directory Selector */}
            <div className="flex-1 max-w-2xl flex items-center gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search files, images with faces, job documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 h-11 bg-input-background"
                />
              </div>

              <Select
                value={selectedDirectory}
                onValueChange={(value) => setSelectedDirectory(value)}
              >
                <SelectTrigger className="w-[280px] h-11 bg-input-background">
                  <SelectValue placeholder="Select directory" />
                </SelectTrigger>
                <SelectContent>
                  {directories.map((dir) => (
                    <SelectItem key={dir} value={dir}>
                      <span className="font-mono text-sm">{dir}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Theme Toggle */}
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto px-6 py-8">
        {statsLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading statistics...</p>
            </div>
          </div>
        ) : stats ? (
          <>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-foreground">
                Analytics for:{" "}
                <span className="text-indigo-600 dark:text-indigo-400 font-mono">
                  {selectedDirectory}
                </span>
              </h2>
              <p className="text-muted-foreground mt-1">
                Real-time insights and statistics for your indexed content
              </p>
            </div>

            {/* Analytics Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Indexing Progress */}
              <IndexingProgress
                totalFiles={stats.totalFiles}
                indexedFiles={stats.indexedFiles}
                filesPerSecond={stats.filesPerSecond}
                estimatedTimeRemaining={stats.estimatedTimeRemaining}
              />

              {/* Storage Overview */}
              <StorageOverview {...stats.storage} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* File Type Distribution */}
              <FileTypeDistribution data={stats.fileTypes} />

              {/* Directory Sizes */}
              <DirectorySizes data={stats.topDirectories} />
            </div>

            {/* Indexing Activity - Full Width */}
            <div className="mb-6">
              <IndexingActivity data={stats.activity} />
            </div>
          </>
        ) : (
          <div className="text-center py-20">
            <p className="text-muted-foreground">No data available for this directory.</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <AppContent />
    </ThemeProvider>
  );
}
