import { useState, useEffect, useCallback } from "react";
import { dataService, DirectoryStats } from "@/app/services/dataService";

export function useDirectories() {
  const [directories, setDirectories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDirectories = async () => {
    try {
      setLoading(true);
      const dirs = await dataService.getDirectories();
      setDirectories(dirs);
      setError(null);
    } catch (err) {
      setError("Failed to load directories");
      console.error(err);
      setDirectories([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDirectories();
  }, []);

  return { directories, loading, error, refresh: fetchDirectories };
}

export function useDirectoryStats(directoryPath: string | null, pollInterval: number = 1000) {
  const [stats, setStats] = useState<DirectoryStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;
    let intervalId: NodeJS.Timeout | null = null;

    const fetchStats = async () => {
      if (!directoryPath) {
        setStats(null);
        setLoading(false);
        return;
      }

      if (isCancelled) return;

      try {
        setLoading(true);
        const data = await dataService.getDirectoryStats(directoryPath);
        
        if (!isCancelled) {
          setStats(data);
          setError(null);
        }
      } catch (err) {
        if (!isCancelled) {
          setError("Failed to load directory statistics");
          console.error(err);
          setStats(null);
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    fetchStats();

    intervalId = setInterval(async () => {
      if (!directoryPath || isCancelled) return;
      
      try {
        const progress = await dataService.getIndexingProgress(directoryPath);
        if (isCancelled) return;
        
        const isIndexing = progress && (progress.status === "indexing" || progress.status === "starting");
        
        if (isIndexing) {
          const data = await dataService.getDirectoryStats(directoryPath);
          if (!isCancelled) {
            setStats(data);
          }
        } else {
          if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
          }
          fetchStats();
        }
      } catch (err) {
        if (!isCancelled) {
          console.error("Error polling stats:", err);
        }
      }
    }, pollInterval);

    return () => {
      isCancelled = true;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [directoryPath, pollInterval]);

  const refresh = useCallback(async () => {
    if (!directoryPath) {
      setStats(null);
      return;
    }

    try {
      setLoading(true);
      const data = await dataService.getDirectoryStats(directoryPath);
      setStats(data);
      setError(null);
    } catch (err) {
      setError("Failed to load directory statistics");
      console.error(err);
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [directoryPath]);

  return { stats, loading, error, refresh };
}
