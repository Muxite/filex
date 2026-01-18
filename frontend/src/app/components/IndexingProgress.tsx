import { Card } from "@/app/components/ui/card";
import { Progress } from "@/app/components/ui/progress";
import { FileSearch, CheckCircle2, Clock } from "lucide-react";

interface IndexingProgressProps {
  totalFiles: number;
  indexedFiles: number;
  filesPerSecond: number;
  estimatedTimeRemaining: string;
}

export function IndexingProgress({
  totalFiles,
  indexedFiles,
  filesPerSecond,
  estimatedTimeRemaining,
}: IndexingProgressProps) {
  const progress = (indexedFiles / totalFiles) * 100;

  return (
    <Card className="p-6 bg-card">
      <div className="flex items-center gap-2 mb-4">
        <FileSearch className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        <h3 className="text-lg font-semibold text-foreground">Indexing Progress</h3>
      </div>

      <div className="space-y-6">
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm text-muted-foreground">
              {indexedFiles.toLocaleString()} / {totalFiles.toLocaleString()} files
            </span>
            <span className="text-sm font-medium text-foreground">{progress.toFixed(1)}%</span>
          </div>
          <Progress value={progress} className="h-3" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Processing Speed</p>
              <p className="text-xl font-semibold text-foreground">{filesPerSecond}</p>
              <p className="text-xs text-muted-foreground">files/sec</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Est. Time Remaining</p>
              <p className="text-xl font-semibold text-foreground">{estimatedTimeRemaining}</p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}