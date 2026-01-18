// Types for the data structure
export interface FileTypeData {
  name: string;
  value: number;
  color: string;
}

export interface DirectorySizeData {
  name: string;
  size: number;
  files: number;
}

export interface IndexingActivityData {
  time: string;
  filesProcessed: number;
  errors: number;
}

export interface StorageData {
  totalSize: number;
  usedSize: number;
  totalFiles: number;
  images: number;
  documents: number;
  media: number;
}

export interface DirectoryStats {
  totalFiles: number;
  indexedFiles: number;
  filesPerSecond: number;
  estimatedTimeRemaining: string;
  fileTypes: FileTypeData[];
  topDirectories: DirectorySizeData[];
  activity: IndexingActivityData[];
  storage: StorageData;
}

export interface DirectoryDataMap {
  [key: string]: DirectoryStats;
}

// Mock data - replace this entire section with API calls
const mockDirectoryData: DirectoryDataMap = {
  "C:\\Users\\Documents": {
    totalFiles: 45230,
    indexedFiles: 45230,
    filesPerSecond: 0,
    estimatedTimeRemaining: "Complete",
    fileTypes: [
      { name: "Documents", value: 18450, color: "#22c55e" },
      { name: "Images", value: 12300, color: "#3b82f6" },
      { name: "Videos", value: 3200, color: "#a855f7" },
      { name: "Audio", value: 4280, color: "#f59e0b" },
      { name: "Archives", value: 2500, color: "#ef4444" },
      { name: "Other", value: 4500, color: "#6b7280" },
    ],
    topDirectories: [
      { name: "Photos", size: 52428800000, files: 8500 },
      { name: "Projects", size: 31457280000, files: 15200 },
      { name: "Work", size: 20971520000, files: 12300 },
      { name: "Personal", size: 15728640000, files: 6800 },
      { name: "Downloads", size: 10485760000, files: 2430 },
    ],
    activity: [
      { time: "00:00", filesProcessed: 1250, errors: 2 },
      { time: "04:00", filesProcessed: 980, errors: 1 },
      { time: "08:00", filesProcessed: 2340, errors: 5 },
      { time: "12:00", filesProcessed: 3120, errors: 3 },
      { time: "16:00", filesProcessed: 2890, errors: 4 },
      { time: "20:00", filesProcessed: 1450, errors: 1 },
    ],
    storage: {
      totalSize: 500000000000,
      usedSize: 131072000000,
      totalFiles: 45230,
      images: 12300,
      documents: 18450,
      media: 7480,
    },
  },
  "D:\\Media": {
    totalFiles: 28650,
    indexedFiles: 24320,
    filesPerSecond: 125,
    estimatedTimeRemaining: "34 min",
    fileTypes: [
      { name: "Images", value: 15200, color: "#3b82f6" },
      { name: "Videos", value: 8430, color: "#a855f7" },
      { name: "Audio", value: 4200, color: "#f59e0b" },
      { name: "Documents", value: 620, color: "#22c55e" },
      { name: "Other", value: 200, color: "#6b7280" },
    ],
    topDirectories: [
      { name: "Movies", size: 157286400000, files: 3240 },
      { name: "TV Shows", size: 104857600000, files: 4850 },
      { name: "Music", size: 41943040000, files: 4200 },
      { name: "Photos", size: 36700160000, files: 15200 },
      { name: "Misc", size: 5242880000, files: 1160 },
    ],
    activity: [
      { time: "00:00", filesProcessed: 890, errors: 0 },
      { time: "04:00", filesProcessed: 1120, errors: 2 },
      { time: "08:00", filesProcessed: 1560, errors: 3 },
      { time: "12:00", filesProcessed: 2340, errors: 1 },
      { time: "16:00", filesProcessed: 3120, errors: 8 },
      { time: "20:00", filesProcessed: 2890, errors: 4 },
    ],
    storage: {
      totalSize: 1000000000000,
      usedSize: 346030080000,
      totalFiles: 28650,
      images: 15200,
      documents: 620,
      media: 12630,
    },
  },
  "C:\\Projects": {
    totalFiles: 67890,
    indexedFiles: 54560,
    filesPerSecond: 89,
    estimatedTimeRemaining: "2 hr 30 min",
    fileTypes: [
      { name: "Documents", value: 32400, color: "#22c55e" },
      { name: "Code Files", value: 18900, color: "#06b6d4" },
      { name: "Images", value: 8200, color: "#3b82f6" },
      { name: "Archives", value: 4390, color: "#ef4444" },
      { name: "Other", value: 4000, color: "#6b7280" },
    ],
    topDirectories: [
      { name: "Client-A", size: 62914560000, files: 23400 },
      { name: "Client-B", size: 52428800000, files: 18900 },
      { name: "Internal", size: 41943040000, files: 15200 },
      { name: "Archive", size: 31457280000, files: 8390 },
      { name: "Resources", size: 10485760000, files: 2000 },
    ],
    activity: [
      { time: "00:00", filesProcessed: 450, errors: 1 },
      { time: "04:00", filesProcessed: 320, errors: 0 },
      { time: "08:00", filesProcessed: 1890, errors: 12 },
      { time: "12:00", filesProcessed: 2560, errors: 8 },
      { time: "16:00", filesProcessed: 3120, errors: 15 },
      { time: "20:00", filesProcessed: 890, errors: 3 },
    ],
    storage: {
      totalSize: 250000000000,
      usedSize: 199229440000,
      totalFiles: 67890,
      images: 8200,
      documents: 32400,
      media: 890,
    },
  },
  "C:\\Users\\John": {
    totalFiles: 156230,
    indexedFiles: 89450,
    filesPerSecond: 156,
    estimatedTimeRemaining: "7 hr 10 min",
    fileTypes: [
      { name: "Images", value: 52300, color: "#3b82f6" },
      { name: "Documents", value: 38900, color: "#22c55e" },
      { name: "Videos", value: 28400, color: "#a855f7" },
      { name: "Audio", value: 18200, color: "#f59e0b" },
      { name: "Archives", value: 12430, color: "#ef4444" },
      { name: "Other", value: 6000, color: "#6b7280" },
    ],
    topDirectories: [
      { name: "Pictures", size: 209715200000, files: 52300 },
      { name: "Videos", size: 157286400000, files: 28400 },
      { name: "Music", size: 94371840000, files: 18200 },
      { name: "Documents", size: 52428800000, files: 38900 },
      { name: "Downloads", size: 41943040000, files: 18430 },
    ],
    activity: [
      { time: "00:00", filesProcessed: 2340, errors: 8 },
      { time: "04:00", filesProcessed: 1890, errors: 5 },
      { time: "08:00", filesProcessed: 3450, errors: 12 },
      { time: "12:00", filesProcessed: 4120, errors: 15 },
      { time: "16:00", filesProcessed: 3890, errors: 10 },
      { time: "20:00", filesProcessed: 2560, errors: 6 },
    ],
    storage: {
      totalSize: 2000000000000,
      usedSize: 555745280000,
      totalFiles: 156230,
      images: 52300,
      documents: 38900,
      media: 46600,
    },
  },
};

// Data Service - Replace these functions with actual API calls
export const dataService = {
  /**
   * Fetch list of available directories
   * API Implementation: GET /api/directories
   */
  async getDirectories(): Promise<string[]> {
    // Mock implementation
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(Object.keys(mockDirectoryData));
      }, 100);
    });
  },

  /**
   * Fetch statistics for a specific directory
   * API Implementation: GET /api/directories/:path/stats
   */
  async getDirectoryStats(directoryPath: string): Promise<DirectoryStats | null> {
    // Mock implementation
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(mockDirectoryData[directoryPath] || null);
      }, 150);
    });
  },

  /**
   * Search files in a directory
   * API Implementation: POST /api/search with body { query, directoryPath }
   */
  async searchFiles(query: string, directoryPath: string): Promise<any[]> {
    // Mock implementation - replace with actual API call
    return new Promise((resolve) => {
      setTimeout(() => {
        // Return mock search results
        resolve([]);
      }, 200);
    });
  },

  /**
   * Get real-time indexing progress
   * API Implementation: GET /api/directories/:path/progress (WebSocket for real-time)
   */
  async getIndexingProgress(directoryPath: string): Promise<{
    totalFiles: number;
    indexedFiles: number;
    filesPerSecond: number;
    estimatedTimeRemaining: string;
  }> {
    // Mock implementation
    return new Promise((resolve) => {
      setTimeout(() => {
        const stats = mockDirectoryData[directoryPath];
        resolve({
          totalFiles: stats?.totalFiles || 0,
          indexedFiles: stats?.indexedFiles || 0,
          filesPerSecond: stats?.filesPerSecond || 0,
          estimatedTimeRemaining: stats?.estimatedTimeRemaining || "Unknown",
        });
      }, 100);
    });
  },
};

// Helper function to convert API response to DirectoryStats format
export function mapApiResponseToDirectoryStats(apiResponse: any): DirectoryStats {
  // Implement mapping logic based on your API response structure
  return apiResponse as DirectoryStats;
}
