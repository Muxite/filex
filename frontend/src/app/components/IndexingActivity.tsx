import { Card } from "@/app/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Activity } from "lucide-react";

interface IndexingActivityData {
  time: string;
  filesProcessed: number;
  errors: number;
}

interface IndexingActivityProps {
  data: IndexingActivityData[];
}

export function IndexingActivity({ data }: IndexingActivityProps) {
  return (
    <Card className="p-6 bg-card">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-green-600 dark:text-green-400" />
        <h3 className="text-lg font-semibold text-foreground">Indexing Activity (Last 24 Hours)</h3>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="filesProcessed"
            stroke="#10b981"
            strokeWidth={2}
            name="Files Processed"
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="errors"
            stroke="#ef4444"
            strokeWidth={2}
            name="Errors"
            dot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}