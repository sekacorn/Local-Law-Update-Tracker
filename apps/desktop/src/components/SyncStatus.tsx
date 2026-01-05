import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export default function SyncStatus() {
  const { data: status } = useQuery({
    queryKey: ['sync-status'],
    queryFn: () => api.get('/api/sync/status'),
    refetchInterval: 2000, // Poll every 2 seconds
  })

  if (!status || status.status === 'none') {
    return null
  }

  const isRunning = status.status === 'running'
  const progress = status.progress || {}

  return (
    <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 w-96 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900 dark:text-white">
          Sync Status
        </h3>
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          isRunning
            ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
            : status.status === 'completed'
            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
        }`}>
          {status.status}
        </span>
      </div>

      {Object.entries(progress).map(([source, info]: [string, any]) => (
        <div key={source} className="mb-2 pb-2 border-b border-gray-200 dark:border-gray-700 last:border-0">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-700 dark:text-gray-300 capitalize">
              {source.replace('_', ' ')}
            </span>
            <span className={`text-xs ${
              info.stage === 'completed'
                ? 'text-green-600 dark:text-green-400'
                : info.stage === 'failed'
                ? 'text-red-600 dark:text-red-400'
                : 'text-blue-600 dark:text-blue-400'
            }`}>
              {info.stage}
            </span>
          </div>

          {info.items_total > 0 && (
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                <div
                  className="bg-blue-600 h-1.5 rounded-full transition-all"
                  style={{ width: `${(info.items_done / info.items_total) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {info.items_done}/{info.items_total}
              </span>
            </div>
          )}

          {info.last_error && (
            <div className="text-xs text-red-600 dark:text-red-400 mt-1">
              Error: {info.last_error}
            </div>
          )}
        </div>
      ))}

      {status.completed_at && (
        <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Completed: {new Date(status.completed_at).toLocaleTimeString()}
        </div>
      )}
    </div>
  )
}
