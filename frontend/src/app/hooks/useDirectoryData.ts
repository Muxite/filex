import { useState, useEffect } from "react";
import { dataService, DirectoryStats } from "@/app/services/dataService";

export function useDirectories() {
  const [directories, setDirectories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDirectories() {
      try {
        setLoading(true);
        const dirs = await dataService.getDirectories();
        setDirectories(dirs);
        setError(null);
      } catch (err) {
        setError("Failed to load directories");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchDirectories();
  }, []);

  return { directories, loading, error };
}

export function useDirectoryStats(directoryPath: string | null) {
  const [stats, setStats] = useState<DirectoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!directoryPath) {
      setStats(null);
      setLoading(false);
      return;
    }

    async function fetchStats() {
      try {
        setLoading(true);
        const data = await dataService.getDirectoryStats(directoryPath);
        setStats(data);
        setError(null);
      } catch (err) {
        setError("Failed to load directory statistics");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();

    // Optional: Set up polling for real-time updates
    // const interval = setInterval(fetchStats, 5000);
    // return () => clearInterval(interval);
  }, [directoryPath]);

  return { stats, loading, error, refresh: () => {} };
}
