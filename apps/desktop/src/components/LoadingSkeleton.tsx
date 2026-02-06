export function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>

      {/* Content Skeletons */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-3">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-4/6"></div>
        </div>
      ))}
    </div>
  )
}

export function ConfidenceLoadingSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 animate-pulse">
      <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-3"></div>
      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
    </div>
  )
}

export function WarningLoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2].map((i) => (
        <div key={i} className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex gap-3">
            <div className="h-8 w-8 bg-red-200 dark:bg-red-800 rounded"></div>
            <div className="flex-1 space-y-2">
              <div className="h-5 bg-red-200 dark:bg-red-800 rounded w-1/4"></div>
              <div className="h-4 bg-red-200 dark:bg-red-800 rounded w-full"></div>
              <div className="h-4 bg-red-200 dark:bg-red-800 rounded w-5/6"></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
