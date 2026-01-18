# FILEX - Semantic File System Search Dashboard

A local analytics dashboard for semantic file system search, designed for Windows file systems.

## Features

- 🔍 **Semantic Search** - Search for files using natural language queries
- 📊 **Real-time Analytics** - View indexing progress, file type distributions, and storage metrics
- 🌙 **Dark Mode** - Optional dark mode support
- 📁 **Multi-Directory Support** - Monitor multiple root directories simultaneously
- 🎨 **Modern UI** - Clean, responsive interface built with React and Tailwind CSS

## Architecture

### Data Service Layer

All data interactions are abstracted through `/src/app/services/dataService.ts`, making it easy to replace mock data with real API calls.

### API Integration Points

Replace the mock implementations in `dataService.ts` with your backend API:

#### 1. Get Directories List
```typescript
// Current: Mock implementation
// Replace with: GET /api/directories
async getDirectories(): Promise<string[]>
```

#### 2. Get Directory Statistics
```typescript
// Current: Mock implementation
// Replace with: GET /api/directories/:path/stats
async getDirectoryStats(directoryPath: string): Promise<DirectoryStats | null>
```

#### 3. Search Files
```typescript
// Current: Mock implementation
// Replace with: POST /api/search
// Body: { query: string, directoryPath: string }
async searchFiles(query: string, directoryPath: string): Promise<any[]>
```

#### 4. Real-time Indexing Progress
```typescript
// Current: Mock implementation
// Replace with: WebSocket connection or polling endpoint
// Recommended: WebSocket at ws://localhost:PORT/api/directories/:path/progress
async getIndexingProgress(directoryPath: string)
```

### Data Types

All TypeScript interfaces are defined in `/src/app/services/dataService.ts`:

- `DirectoryStats` - Complete statistics for a directory
- `FileTypeData` - File type distribution data
- `DirectorySizeData` - Directory size information
- `IndexingActivityData` - Indexing activity timeline
- `StorageData` - Storage usage information

### Custom Hooks

Use the provided hooks for data fetching:

```typescript
import { useDirectories, useDirectoryStats } from "@/app/hooks/useDirectoryData";

// In your component:
const { directories, loading, error } = useDirectories();
const { stats, loading, error } = useDirectoryStats(selectedDirectory);
```

## Mock Data

The current implementation uses Windows-style paths:
- `C:\Users\Documents`
- `D:\Media`
- `C:\Projects`
- `C:\Users\John`

Replace these with actual paths from your file system.

## Running the Application

```bash
npm install
npm run dev
```

## Customization

### Theme
- Light and dark mode supported out of the box
- Toggle theme using the moon/sun icon in the header
- Theme preference is persisted via `next-themes`

### Branding
- Logo and title can be customized in `/src/app/App.tsx`
- Current branding: "FILEX" with wide letter spacing

### Colors
- Color scheme defined in `/src/styles/theme.css`
- Charts use consistent color palette across light/dark modes

## Technologies

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS v4** - Styling
- **Recharts** - Data visualization
- **Radix UI** - Accessible components
- **next-themes** - Dark mode support
- **Lucide React** - Icons

## Future Enhancements

- Real-time updates via WebSocket
- Advanced search filters
- Export analytics data
- File preview functionality
- Multi-language support
