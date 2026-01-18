/**
 * Data service for FileX API integration.
 * 
 * Connects to the FastAPI backend at http://127.0.0.1:8000
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

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

export interface Repository {
  repo_path: string;
  work_tree: string;
  name: string;
}

export interface SearchResult {
  file_path: string;
  file_name: string;
  chunk_index: number;
  chunk_text: string;
  similarity_score: number;
  image_data?: string;
  image_size_mb?: number;
  image_error?: string;
}

export interface IndexProgress {
  status: "starting" | "indexing" | "completed" | "error";
  indexed: number;
  total: number;
  errors: number;
  error?: string;
}

export interface PathValidation {
  isValid: boolean;
  message: string;
  repo_path?: string;
  work_tree?: string;
}

export interface ApiStats {
  repository_path: string;
  work_tree: string;
  index_statistics: {
    total_indexed_files: number;
    text_files: number;
    image_files: number;
    non_text_files: number;
    total_chunks: number;
  };
  search_statistics: {
    total_chunks: number;
    unique_files: number;
    embedding_dimension: number | null;
  };
  storage_statistics: {
    embeddings_bytes: number;
    embeddings_mb: number;
    metadata_bytes: number;
    metadata_kb: number;
    total_bytes: number;
    total_mb: number;
  };
  file_types: {
    [ext: string]: {
      count: number;
      total_size: number;
      total_chunks: number;
    };
  };
  eligible_files_count: number;
  eligible_file_types?: {
    [ext: string]: {
      count: number;
      total_size: number;
    };
  };
  eligible_statistics?: {
    total_files: number;
    text_files: number;
    image_files: number;
    total_size_bytes: number;
    total_size_mb: number;
  };
}

const FILE_TYPE_COLORS: { [key: string]: string } = {
  ".txt": "#22c55e",
  ".docx": "#22c55e",
  ".png": "#3b82f6",
  ".jpg": "#3b82f6",
  ".jpeg": "#3b82f6",
  ".mp4": "#a855f7",
  ".avi": "#a855f7",
  ".mov": "#a855f7",
  ".mp3": "#f59e0b",
  ".wav": "#f59e0b",
  ".zip": "#ef4444",
  ".rar": "#ef4444",
  ".tar": "#ef4444",
  "other": "#6b7280",
};

function getFileTypeColor(extension: string): string {
  return FILE_TYPE_COLORS[extension.toLowerCase()] || FILE_TYPE_COLORS["other"];
}

function formatFileTypeName(extension: string): string {
  const ext = extension.toLowerCase();
  if (ext === ".txt" || ext === ".docx") return "Documents";
  if (ext === ".png" || ext === ".jpg" || ext === ".jpeg") return "Images";
  if (ext === ".mp4" || ext === ".avi" || ext === ".mov") return "Videos";
  if (ext === ".mp3" || ext === ".wav") return "Audio";
  if (ext === ".zip" || ext === ".rar" || ext === ".tar") return "Archives";
  return "Other";
}

function mapApiStatsToDirectoryStats(apiStats: ApiStats, progress?: IndexProgress): DirectoryStats {
  const fileTypes: FileTypeData[] = [];
  const typeMap: { [key: string]: { count: number; size: number } } = {};

  const sourceFileTypes = apiStats.file_types && Object.keys(apiStats.file_types).length > 0
    ? apiStats.file_types
    : apiStats.eligible_file_types || {};

  for (const [ext, data] of Object.entries(sourceFileTypes)) {
    const typeName = formatFileTypeName(ext);
    if (!typeMap[typeName]) {
      typeMap[typeName] = { count: 0, size: 0 };
    }
    typeMap[typeName].count += data.count;
    typeMap[typeName].size += data.total_size || 0;
  }

  for (const [typeName, data] of Object.entries(typeMap)) {
    const ext = Object.keys(sourceFileTypes).find(
      (e) => formatFileTypeName(e) === typeName
    ) || ".other";
    fileTypes.push({
      name: typeName,
      value: data.count,
      color: getFileTypeColor(ext),
    });
  }

  const indexedFiles = progress
    ? progress.indexed
    : apiStats.index_statistics.total_indexed_files;

  const totalFiles = progress
    ? progress.total
    : (apiStats.eligible_statistics?.total_files ?? apiStats.eligible_files_count);

  const filesPerSecond = progress && progress.status === "indexing"
    ? Math.round((progress.indexed / (Date.now() / 1000)) * 10) / 10
    : 0;

  const remaining = totalFiles - indexedFiles;
  const estimatedTimeRemaining =
    filesPerSecond > 0 && remaining > 0
      ? `${Math.ceil(remaining / filesPerSecond)} sec`
      : indexedFiles >= totalFiles
      ? "Complete"
      : "Unknown";

  const topDirectories: DirectorySizeData[] = [];
  const dirMap: { [key: string]: { size: number; files: number } } = {};

  for (const [ext, data] of Object.entries(sourceFileTypes)) {
    const dirName = ext.substring(1).toUpperCase() + " Files";
    if (!dirMap[dirName]) {
      dirMap[dirName] = { size: 0, files: 0 };
    }
    dirMap[dirName].size += data.total_size || 0;
    dirMap[dirName].files += data.count;
  }

  for (const [name, data] of Object.entries(dirMap)) {
    topDirectories.push({
      name,
      size: data.size,
      files: data.files,
    });
  }

  topDirectories.sort((a, b) => b.size - a.size);
  topDirectories.splice(5);

  const activity: IndexingActivityData[] = [];
  if (progress && progress.status === "indexing") {
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;
    activity.push({
      time: timeStr,
      filesProcessed: progress.indexed,
      errors: progress.errors,
    });
  }

  return {
    totalFiles,
    indexedFiles,
    filesPerSecond,
    estimatedTimeRemaining,
    fileTypes,
    topDirectories,
    activity,
    storage: {
      totalSize: (apiStats.eligible_statistics?.total_size_bytes || apiStats.storage_statistics.total_bytes) * 10,
      usedSize: apiStats.storage_statistics.total_bytes || 0,
      totalFiles: apiStats.index_statistics.total_indexed_files || 0,
      images: apiStats.index_statistics.image_files || (apiStats.eligible_statistics?.image_files || 0),
      documents: apiStats.index_statistics.text_files || (apiStats.eligible_statistics?.text_files || 0),
      media: (apiStats.index_statistics.non_text_files - apiStats.index_statistics.image_files) || 0,
    },
  };
}

export const dataService = {
  /**
   * Fetch list of available repositories.
   * API: GET /api/repositories
   */
  async getDirectories(): Promise<string[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/repositories`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.repositories.map((repo: Repository) => repo.work_tree);
    } catch (error) {
      console.error("Error fetching directories:", error);
      return [];
    }
  },

  async getRegisteredFolders(): Promise<string[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/registered-folders`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.folders || [];
    } catch (error) {
      console.error("Error fetching registered folders:", error);
      return [];
    }
  },

  async registerFolder(path: string): Promise<{ success: boolean; message: string; folders?: string[] }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/registered-folders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ path }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        message: data.message || "Folder registered successfully",
        folders: data.folders,
      };
    } catch (error) {
      console.error("Error registering folder:", error);
      return {
        success: false,
        message: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  async unregisterFolder(path: string): Promise<{ success: boolean; message: string }> {
    try {
      const encodedPath = encodeURIComponent(path);
      const response = await fetch(`${API_BASE_URL}/api/registered-folders/${encodedPath}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        message: data.message || "Folder unregistered successfully",
      };
    } catch (error) {
      console.error("Error unregistering folder:", error);
      return {
        success: false,
        message: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  /**
   * Get repository information.
   * API: GET /api/repositories
   */
  async getRepositories(): Promise<Repository[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/repositories`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.repositories;
    } catch (error) {
      console.error("Error fetching repositories:", error);
      return [];
    }
  },

  /**
   * Fetch statistics for a specific repository.
   * API: POST /api/stats
   */
  async getDirectoryStats(directoryPath: string): Promise<DirectoryStats | null> {
    try {
      if (!directoryPath || !directoryPath.trim()) {
        return null;
      }
      
      const response = await fetch(`${API_BASE_URL}/api/stats`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo_path: directoryPath,
        }),
      });

      if (!response.ok) {
        if (response.status === 404 || response.status === 400) {
          const errorData = await response.json().catch(() => ({ detail: "Path not found" }));
          console.warn(`Stats not available: ${errorData.detail || "Path not found"}`);
          return null;
        }
        if (response.status === 500) {
          const errorData = await response.json().catch(() => ({ detail: "Server error" }));
          console.error(`Server error getting stats: ${errorData.detail || "Unknown error"}`);
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const apiStats: ApiStats = await response.json();
      
      const progress = await this.getIndexingProgress(directoryPath).catch(() => null);
      
      return mapApiStatsToDirectoryStats(apiStats, progress || undefined);
    } catch (error) {
      console.error("Error fetching directory statistics:", error);
      return null;
    }
  },

  /**
   * Search files in a repository.
   * API: POST /api/search
   */
  async searchFiles(
    query: string,
    directoryPath: string,
    topK: number = 10,
    includeImages: boolean = false
  ): Promise<SearchResult[]> {
    try {
      const repos = await this.getRepositories();
      const repo = repos.find((r) => r.work_tree === directoryPath);
      
      const response = await fetch(`${API_BASE_URL}/api/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo_path: repo ? repo.repo_path : directoryPath,
          query,
          top_k: topK,
          include_images: includeImages,
          max_image_size_mb: 1.0,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.results || [];
    } catch (error) {
      console.error("Error searching files:", error);
      throw error;
    }
  },

  /**
   * Get real-time indexing progress.
   * API: GET /api/progress/{repo_id}
   */
  async getIndexingProgress(directoryPath: string): Promise<IndexProgress | null> {
    try {
      const repoId = encodeURIComponent(directoryPath);
      const response = await fetch(`${API_BASE_URL}/api/progress/${repoId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.status === "not_found") {
        return null;
      }
      
      return data as IndexProgress;
    } catch (error) {
      console.error("Error fetching indexing progress:", error);
      return null;
    }
  },

  /**
   * Start indexing for a specific repository.
   * API: POST /api/index
   */
  async startIndexing(
    directoryPath: string,
    path?: string,
    force: boolean = false
  ): Promise<{ success: boolean; message: string; task_id?: string }> {
    try {
      const repos = await this.getRepositories();
      const repo = repos.find((r) => r.work_tree === directoryPath);
      
      const response = await fetch(`${API_BASE_URL}/api/index`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo_path: repo ? repo.repo_path : directoryPath,
          path: path,
          force: force,
          recursive: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        message: data.message || "Indexing started successfully",
        task_id: data.task_id,
      };
    } catch (error) {
      console.error("Error starting indexing:", error);
      return {
        success: false,
        message: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  /**
   * Force re-index all files in a repository.
   * API: POST /api/index with force=true
   */
  async forceIndexAll(directoryPath: string): Promise<{ success: boolean; message: string }> {
    return this.startIndexing(directoryPath, undefined, true);
  },

  /**
   * Validate a directory path and check if it can be used for indexing.
   * API: POST /api/stats (to test if path is valid)
   */
  async validatePath(directoryPath: string): Promise<PathValidation> {
    if (!directoryPath || !directoryPath.trim()) {
      return {
        isValid: false,
        message: "Path cannot be empty",
      };
    }

    const path = directoryPath.trim();
    try {
      const response = await fetch(`${API_BASE_URL}/api/stats`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo_path: path,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        return {
          isValid: true,
          message: "Path is valid and ready for indexing",
          repo_path: data.repository_path,
          work_tree: data.work_tree,
        };
      }

      const status = response.status;
      const errorData = await response.json().catch(() => ({ detail: "Path is not valid" }));
      
      if (status === 404) {
        return {
          isValid: false,
          message: `Path does not exist: ${path}`,
        };
      } else if (status === 400) {
        return {
          isValid: false,
          message: errorData.detail || `Invalid path: ${path}`,
        };
      } else {
        return {
          isValid: false,
          message: errorData.detail || "Path not found or not accessible",
        };
      }
    } catch (error) {
      return {
        isValid: false,
        message: error instanceof Error ? error.message : "Error validating path",
      };
    }
  },
};
