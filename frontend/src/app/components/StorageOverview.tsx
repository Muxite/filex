import { Card } from "@/app/components/ui/card";
import { HardDrive, File, Image, FileText, Music } from "lucide-react";

interface StorageOverviewProps {
  totalSize: number;
  usedSize: number;
  totalFiles: number;
  images: number;
  documents: number;
  media: number;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

export function StorageOverview({
  totalSize,
  usedSize,
  totalFiles,
  images,
  documents,
  media,
}: StorageOverviewProps) {
  const usagePercent = (usedSize / totalSize) * 100;

  return (
    <Card className="p-6 bg-card">
      <div className="flex items-center gap-2 mb-6">
        <HardDrive className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
        <h3 className="text-lg font-semibold text-foreground">Storage Overview</h3>
      </div>

      <div className="space-y-6">
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm text-muted-foreground">Storage Used</span>
            <span className="text-sm font-medium text-foreground">
              {formatBytes(usedSize)} / {formatBytes(totalSize)}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div
              className="bg-indigo-600 dark:bg-indigo-500 h-3 rounded-full transition-all"
              style={{ width: `${usagePercent}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-1">{usagePercent.toFixed(1)}% used</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <File className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <div>
              <p className="text-xs text-muted-foreground">Total Files</p>
              <p className="text-lg font-semibold text-foreground">{totalFiles.toLocaleString()}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
            <Image className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <div>
              <p className="text-xs text-muted-foreground">Images</p>
              <p className="text-lg font-semibold text-foreground">{images.toLocaleString()}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-900/30 rounded-lg">
            <FileText className="w-5 h-5 text-green-600 dark:text-green-400" />
            <div>
              <p className="text-xs text-muted-foreground">Documents</p>
              <p className="text-lg font-semibold text-foreground">{documents.toLocaleString()}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-purple-50 dark:bg-purple-900/30 rounded-lg">
            <Music className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <div>
              <p className="text-xs text-muted-foreground">Media</p>
              <p className="text-lg font-semibold text-foreground">{media.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}