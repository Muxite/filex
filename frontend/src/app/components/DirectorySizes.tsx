import { Card } from "@/app/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { FolderOpen } from "lucide-react";

interface DirectorySizeData {
  name: string;
  size: number;
  files: number;
}

interface DirectorySizesProps {
  data: DirectorySizeData[];
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

export function DirectorySizes({ data }: DirectorySizesProps) {
  return (
    <Card className="p-6 bg-card">
      <div className="flex items-center gap-2 mb-4">
        <FolderOpen className="w-5 h-5 text-orange-600 dark:text-orange-400" />
        <h3 className="text-lg font-semibold text-foreground">Top Directories by Size</h3>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="horizontal">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" tickFormatter={(value) => formatBytes(value)} />
          <YAxis dataKey="name" type="category" width={100} />
          <Tooltip
            formatter={(value: number) => [formatBytes(value), "Size"]}
            labelFormatter={(label) => `Directory: ${label}`}
          />
          <Legend />
          <Bar dataKey="size" fill="#f97316" name="Size" />
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 space-y-2">
        {data.map((dir, index) => (
          <div key={dir.name} className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-muted-foreground">#{index + 1}</span>
              <span className="text-sm font-medium text-foreground">{dir.name}</span>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-foreground">{formatBytes(dir.size)}</p>
              <p className="text-xs text-muted-foreground">{dir.files.toLocaleString()} files</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}