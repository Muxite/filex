import { ThemeProvider } from "next-themes";
import { useState, useEffect } from "react";
import { Search, FolderOpen, Play, RotateCw, X, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { Input } from "@/app/components/ui/input";
import { Button } from "@/app/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { IndexingProgress } from "@/app/components/IndexingProgress";
import { FileTypeDistribution } from "@/app/components/FileTypeDistribution";
import { DirectorySizes } from "@/app/components/DirectorySizes";
import { IndexingActivity } from "@/app/components/IndexingActivity";
import { StorageOverview } from "@/app/components/StorageOverview";
import { ThemeToggle } from "@/app/components/ThemeToggle";
import { useDirectoryStats } from "@/app/hooks/useDirectoryData";
import { dataService, SearchResult } from "@/app/services/dataService";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select";

function AppContent() {
  const [selectedDirectoryPath, setSelectedDirectoryPath] = useState<string>("");
  const [registeredFolders, setRegisteredFolders] = useState<string[]>([]);
  const [isLoadingFolders, setIsLoadingFolders] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexingProgressInterval, setIndexingProgressInterval] = useState<NodeJS.Timeout | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [pathValidation, setPathValidation] = useState<{ isValid: boolean; message: string } | null>(null);
  const [isValidatingPath, setIsValidatingPath] = useState(false);

  const loadRegisteredFolders = async () => {
    setIsLoadingFolders(true);
    try {
      const folders = await dataService.getRegisteredFolders();
      setRegisteredFolders(folders || []);
    } catch (error) {
      console.error("Error loading registered folders:", error);
      setRegisteredFolders([]);
    } finally {
      setIsLoadingFolders(false);
    }
  };

  useEffect(() => {
    loadRegisteredFolders();
  }, []);

  const validatePath = async (path: string) => {
    if (!path.trim()) {
      setPathValidation(null);
      return;
    }

    setIsValidatingPath(true);
    try {
      const validation = await dataService.validatePath(path);
      setPathValidation(validation);
    } catch (error) {
      setPathValidation({
        isValid: false,
        message: error instanceof Error ? error.message : "Error validating path",
      });
    } finally {
      setIsValidatingPath(false);
    }
  };

  useEffect(() => {
    if (selectedDirectoryPath) {
      validatePath(selectedDirectoryPath);
    } else {
      setPathValidation(null);
    }
  }, [selectedDirectoryPath]);

  const getCurrentDirectory = () => {
    return selectedDirectoryPath;
  };

  const currentDirectory = getCurrentDirectory();
  const { stats, loading: statsLoading, refresh: refreshStats } = useDirectoryStats(
    currentDirectory
  );

  const handleIndex = async () => {
    const currentDir = getCurrentDirectory();
    if (!currentDir) {
      alert("Please select or enter a directory path");
      return;
    }
    
    if (!pathValidation || !pathValidation.isValid) {
      alert("Please enter a valid directory path before indexing. The path must exist and be a directory.");
      return;
    }
    
    if (indexingProgressInterval) {
      clearInterval(indexingProgressInterval);
    }
    
    setIsIndexing(true);
    try {
      const result = await dataService.startIndexing(currentDir);
      if (result.success) {
        console.log(result.message);
        refreshStats();
        
        const checkProgress = setInterval(async () => {
          const progress = await dataService.getIndexingProgress(currentDir);
          if (!progress || progress.status === "completed" || progress.status === "error") {
            clearInterval(checkProgress);
            setIndexingProgressInterval(null);
            setIsIndexing(false);
            refreshStats();
          }
        }, 1000);
        setIndexingProgressInterval(checkProgress);
      } else {
        console.error(result.message);
        alert(result.message);
        setIsIndexing(false);
      }
    } catch (error) {
      console.error("Error starting index:", error);
      alert(`Error starting index: ${error instanceof Error ? error.message : "Unknown error"}`);
      setIsIndexing(false);
    }
  };

  const handleForceIndexAll = async () => {
    const currentDir = getCurrentDirectory();
    if (!currentDir) {
      alert("Please select or enter a directory path");
      return;
    }
    
    if (!pathValidation || !pathValidation.isValid) {
      alert("Please enter a valid directory path before indexing. The path must exist and be a directory.");
      return;
    }
    
    if (indexingProgressInterval) {
      clearInterval(indexingProgressInterval);
    }
    
    setIsIndexing(true);
    try {
      const result = await dataService.forceIndexAll(currentDir);
      if (result.success) {
        console.log(result.message);
        refreshStats();
        
        const checkProgress = setInterval(async () => {
          const progress = await dataService.getIndexingProgress(currentDir);
          if (!progress || progress.status === "completed" || progress.status === "error") {
            clearInterval(checkProgress);
            setIndexingProgressInterval(null);
            setIsIndexing(false);
            refreshStats();
          }
        }, 1000);
        setIndexingProgressInterval(checkProgress);
      } else {
        console.error(result.message);
        alert(result.message);
        setIsIndexing(false);
      }
    } catch (error) {
      console.error("Error force indexing:", error);
      alert(`Error force indexing: ${error instanceof Error ? error.message : "Unknown error"}`);
      setIsIndexing(false);
    }
  };

  const handleSearch = async () => {
    const currentDir = getCurrentDirectory();
    if (!searchQuery.trim() || !currentDir) {
      if (!currentDir) {
        alert("Please select or enter a directory path");
      }
      return;
    }
    
    setIsSearching(true);
    setShowSearchResults(true);
    try {
      const results = await dataService.searchFiles(searchQuery, currentDir, 10, true);
      setSearchResults(results);
    } catch (error) {
      console.error("Error searching:", error);
      setSearchResults([]);
      alert(`Error searching: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };


  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border sticky top-0 z-10 shadow-sm">
        <div className="max-w-[1600px] mx-auto px-6 py-5">
          <div className="flex items-center justify-between gap-6">
            {/* Logo/Title - FILEX with wide styling */}
            <div className="flex items-center gap-3 flex-shrink-0">
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

            {/* Directory Path and Indexing Controls */}
            <div className="flex-1 flex items-center gap-3">
              <div className="flex items-center gap-2 flex-1 max-w-3xl">
                <div className="relative flex-1 flex items-center gap-2">
                  <Select
                    value={selectedDirectoryPath || undefined}
                    onValueChange={(value) => setSelectedDirectoryPath(value)}
                    disabled={isLoadingFolders}
                  >
                    <SelectTrigger className="h-14 text-base bg-input-background font-mono text-sm flex-1">
                      <SelectValue placeholder="Select a folder..." />
                    </SelectTrigger>
                    <SelectContent>
                      {registeredFolders.length === 0 ? (
                        <SelectItem value="__empty__" disabled>No folders registered</SelectItem>
                      ) : (
                        registeredFolders.map((folder) => (
                          <SelectItem key={folder} value={folder} className="font-mono text-sm">
                            {folder}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                  <div className="flex-shrink-0">
                    {isValidatingPath ? (
                      <Loader2 className="w-5 h-5 text-muted-foreground animate-spin" />
                    ) : pathValidation?.isValid ? (
                      <CheckCircle2 className="w-5 h-5 text-green-500" title={pathValidation.message} />
                    ) : pathValidation?.isValid === false ? (
                      <AlertCircle className="w-5 h-5 text-red-500" title={pathValidation.message} />
                    ) : null}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <Button
                  variant="outline"
                  size="default"
                  onClick={handleForceIndexAll}
                  disabled={isIndexing || !getCurrentDirectory() || !pathValidation?.isValid}
                  className="h-14"
                >
                  <RotateCw className={`w-4 h-4 mr-2 ${isIndexing ? 'animate-spin' : ''}`} />
                  Force Index All
                </Button>
                
                <Button
                  size="default"
                  onClick={handleIndex}
                  disabled={isIndexing || !getCurrentDirectory() || !pathValidation?.isValid}
                  className="h-14 bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Index
                </Button>

                <ThemeToggle />
              </div>
            </div>
          </div>

          {/* Search Bar - Below Directory Controls */}
          <div className="mt-4 flex items-center gap-3 w-full">
            <div className="relative flex-[2]">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-6 h-6 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search files, images with faces, job documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleSearchKeyPress}
                className="pl-12 pr-12 h-16 text-lg bg-input-background"
              />
              {searchQuery && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSearchQuery("");
                    setShowSearchResults(false);
                    setSearchResults([]);
                  }}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>
            <Button
              onClick={handleSearch}
              disabled={!searchQuery.trim() || isSearching || !getCurrentDirectory() || !pathValidation?.isValid}
              className="h-16 px-8 bg-blue-600 hover:bg-blue-700 text-white flex-[0.3]"
            >
              {isSearching ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Search
                </>
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto px-6 py-8">
        {showSearchResults && searchResults.length > 0 ? (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-foreground">
                Search Results ({searchResults.length})
              </h2>
              <Button
                variant="outline"
                onClick={() => {
                  setShowSearchResults(false);
                  setSearchResults([]);
                }}
              >
                <X className="w-4 h-4 mr-2" />
                Clear Results
              </Button>
            </div>
            <div className="space-y-4">
              {searchResults.map((result, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{result.file_name}</CardTitle>
                        <CardDescription className="font-mono text-xs mt-1">
                          {result.file_path}
                        </CardDescription>
                      </div>
                      <div className="ml-4 text-right">
                        <div className="text-sm font-semibold text-blue-600">
                          {(result.similarity_score * 100).toFixed(1)}% match
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Chunk {result.chunk_index}
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-foreground line-clamp-3">
                      {result.chunk_text}
                    </p>
                    {result.image_data && (
                      <div className="mt-4">
                        <img
                          src={result.image_data}
                          alt={result.file_name}
                          className="max-w-md max-h-64 rounded-md border border-border"
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ) : showSearchResults && !isSearching ? (
          <div className="text-center py-20">
            <p className="text-muted-foreground">No results found for your search query.</p>
          </div>
        ) : statsLoading ? (
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
                FILEX Repository:{" "}
                <span className="text-indigo-600 dark:text-indigo-400 font-mono">
                  {getCurrentDirectory()}
                </span>
              </h2>
              <p className="text-muted-foreground mt-1">
                Real-time insights and statistics for your indexed content
              </p>
            </div>

            {/* Statistics Grid */}
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