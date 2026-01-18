import { Card } from "@/app/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { FileType } from "lucide-react";

interface FileTypeData {
  name: string;
  value: number;
  color: string;
}

interface FileTypeDistributionProps {
  data: FileTypeData[];
}

export function FileTypeDistribution({ data }: FileTypeDistributionProps) {
  const totalFiles = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <Card className="p-6 bg-card">
      <div className="flex items-center gap-2 mb-4">
        <FileType className="w-5 h-5 text-purple-600 dark:text-purple-400" />
        <h3 className="text-lg font-semibold text-foreground">File Type Distribution</h3>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => [
              `${value.toLocaleString()} files (${((value / totalFiles) * 100).toFixed(1)}%)`,
              "",
            ]}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-2 gap-3">
        {data.map((item) => (
          <div key={item.name} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm text-muted-foreground">{item.name}</span>
            </div>
            <span className="text-sm font-medium text-foreground">{item.value.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}