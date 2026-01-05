import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../lib/api'

export default function Settings() {
  const queryClient = useQueryClient()
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [showClearUploadsConfirm, setShowClearUploadsConfirm] = useState(false)
  const [localSettings, setLocalSettings] = useState<any>(null)

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => api.get('/api/settings'),
    onSuccess: (data) => {
      if (!localSettings) {
        setLocalSettings(data)
      }
    },
  })

  const { data: storageStats } = useQuery({
    queryKey: ['storage-stats'],
    queryFn: () => api.get('/api/uploads/storage/stats'),
  })

  const resetDbMutation = useMutation({
    mutationFn: () => api.post('/api/db/reset', { confirm: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['db-status'] })
      setShowResetConfirm(false)
      alert('Database reset successfully!')
    },
    onError: (error: any) => {
      alert(`Failed to reset database: ${error.message}`)
    },
  })

  const syncMutation = useMutation({
    mutationFn: () => api.post('/api/sync/run', { sources: null }),
    onSuccess: () => {
      alert('Sync started! Check the dashboard for progress.')
    },
    onError: (error: any) => {
      alert(`Failed to start sync: ${error.message}`)
    },
  })

  const saveSettingsMutation = useMutation({
    mutationFn: (newSettings: any) => api.post('/api/settings', { settings: newSettings }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      alert('Settings saved successfully!')
    },
    onError: (error: any) => {
      alert(`Failed to save settings: ${error.message}`)
    },
  })

  const clearUploadsMutation = useMutation({
    mutationFn: () => api.delete('/api/uploads/storage/clear?confirm=true'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['storage-stats'] })
      queryClient.invalidateQueries({ queryKey: ['recent-uploads'] })
      queryClient.invalidateQueries({ queryKey: ['db-status'] })
      setShowClearUploadsConfirm(false)
      alert('All uploads cleared successfully!')
    },
    onError: (error: any) => {
      alert(`Failed to clear uploads: ${error.message}`)
    },
  })

  const handleSaveSettings = () => {
    if (localSettings) {
      saveSettingsMutation.mutate(localSettings)
    }
  }

  const updateSource = (sourceId: string, field: string, value: any) => {
    setLocalSettings((prev: any) => ({
      ...prev,
      sources: {
        ...prev.sources,
        [sourceId]: {
          ...prev.sources[sourceId],
          [field]: value,
        },
      },
    }))
  }

  const updateStorageMode = (mode: string) => {
    setLocalSettings((prev: any) => ({
      ...prev,
      storage_mode: mode,
    }))
  }

  if (isLoading || !localSettings) {
    return <div className="p-8">Loading settings...</div>
  }

  const hasChanges = JSON.stringify(settings) !== JSON.stringify(localSettings)

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        {hasChanges && (
          <button
            onClick={handleSaveSettings}
            disabled={saveSettingsMutation.isPending}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg
                     font-medium disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
          >
            {saveSettingsMutation.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        )}
      </div>

      {/* Storage Mode */}
      <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Storage Mode
        </h2>
        <div className="space-y-2">
          <label className="flex items-center gap-3">
            <input
              type="radio"
              name="storage_mode"
              value="full"
              checked={localSettings?.storage_mode === 'full'}
              onChange={(e) => updateStorageMode(e.target.value)}
              className="text-blue-600"
            />
            <div>
              <div className="font-medium text-gray-900 dark:text-white">
                Full Offline
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Store complete documents locally
              </div>
            </div>
          </label>
          <label className="flex items-center gap-3">
            <input
              type="radio"
              name="storage_mode"
              value="thin"
              checked={localSettings?.storage_mode === 'thin'}
              onChange={(e) => updateStorageMode(e.target.value)}
              className="text-blue-600"
            />
            <div>
              <div className="font-medium text-gray-900 dark:text-white">
                Thin Cache
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Store only metadata and snippets
              </div>
            </div>
          </label>
          <label className="flex items-center gap-3">
            <input
              type="radio"
              name="storage_mode"
              value="meta"
              checked={localSettings?.storage_mode === 'meta'}
              onChange={(e) => updateStorageMode(e.target.value)}
              className="text-blue-600"
            />
            <div>
              <div className="font-medium text-gray-900 dark:text-white">
                Metadata Only
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Store only metadata, fetch content on-demand
              </div>
            </div>
          </label>
        </div>
      </section>

      {/* User Uploads Storage */}
      <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          User Uploads Storage
        </h2>

        {storageStats ? (
          <div className="space-y-4">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">
                  Total Documents
                </div>
                <div className="text-2xl font-bold text-blue-800 dark:text-blue-200">
                  {storageStats.total_uploads}
                </div>
              </div>

              <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                <div className="text-sm text-purple-600 dark:text-purple-400 mb-1">
                  Storage Used
                </div>
                <div className="text-2xl font-bold text-purple-800 dark:text-purple-200">
                  {storageStats.total_size_mb.toFixed(2)} MB
                </div>
              </div>
            </div>

            {/* File Type Breakdown */}
            {Object.keys(storageStats.by_type).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  By File Type
                </h3>
                <div className="space-y-2">
                  {Object.entries(storageStats.by_type).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">
                        {getFileTypeName(type)}
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {count} {count === 1 ? 'file' : 'files'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Storage Mode */}
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                Current Storage Mode
              </div>
              <div className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                {storageStats.storage_mode}
              </div>
            </div>

            {/* Clear All Button */}
            {storageStats.total_uploads > 0 && (
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => setShowClearUploadsConfirm(true)}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg
                           font-medium transition-colors text-sm"
                >
                  Clear All Uploads
                </button>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                  ⚠️ This will permanently delete all uploaded documents and their analysis
                </p>
              </div>
            )}

            {storageStats.total_uploads === 0 && (
              <div className="text-center py-6 text-gray-500 dark:text-gray-400 text-sm">
                No uploaded documents yet. Upload your first document from the Dashboard.
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-600 dark:text-gray-400 text-sm">
            Loading storage statistics...
          </div>
        )}
      </section>

      {/* Data Sources */}
      <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Data Sources
        </h2>
        <div className="space-y-6">
          {localSettings?.sources && Object.entries(localSettings.sources).map(([key, source]: [string, any]) => {
            const needsApiKey = key === 'congress_gov' || key === 'govinfo'
            const hasApiKey = source.api_key && source.api_key !== 'DEMO_KEY'

            return (
              <div key={key} className="pb-6 border-b border-gray-200 dark:border-gray-700 last:border-0">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="font-medium text-gray-900 dark:text-white capitalize">
                      {key.replace(/_/g, ' ')}
                    </div>
                    {needsApiKey && !hasApiKey && (
                      <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded">
                        API Key Required
                      </span>
                    )}
                    {hasApiKey && (
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded">
                        Configured
                      </span>
                    )}
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={source.enabled}
                      onChange={(e) => updateSource(key, 'enabled', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4
                                  peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer
                                  dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white
                                  after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white
                                  after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all
                                  dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                {needsApiKey && (
                  <div className="mt-3">
                    <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">
                      API Key {key === 'congress_gov' ? '(get from api.congress.gov/sign-up)' : '(get from govinfo.gov/api-signup)'}
                    </label>
                    <input
                      type="password"
                      value={source.api_key || ''}
                      onChange={(e) => updateSource(key, 'api_key', e.target.value)}
                      placeholder="Enter API key..."
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600
                               bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                               rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}

                <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  Poll interval: {source.poll_interval_minutes} minutes
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* Actions */}
      <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Actions
        </h2>
        <div className="space-y-4">
          <div>
            <button
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg
                       font-medium disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors"
            >
              {syncMutation.isPending ? 'Starting Sync...' : 'Sync Now'}
            </button>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Fetch new documents from enabled sources
            </p>
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setShowResetConfirm(true)}
              className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg
                       font-medium transition-colors"
            >
              Reset Database
            </button>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              ⚠️ Warning: This will delete all downloaded documents and metadata
            </p>
          </div>
        </div>
      </section>

      {/* Reset Confirmation Modal */}
      {showResetConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Confirm Database Reset
            </h3>
            <p className="text-gray-700 dark:text-gray-300 mb-6">
              Are you sure you want to reset the database? This will delete all
              downloaded documents, versions, and change history. This action
              cannot be undone.
            </p>
            <div className="flex gap-4">
              <button
                onClick={() => setShowResetConfirm(false)}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900
                         dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                onClick={() => resetDbMutation.mutate()}
                disabled={resetDbMutation.isPending}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg
                         disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {resetDbMutation.isPending ? 'Resetting...' : 'Reset Database'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clear Uploads Confirmation Modal */}
      {showClearUploadsConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Clear All Uploads?
            </h3>
            <p className="text-gray-700 dark:text-gray-300 mb-6">
              This will permanently delete all {storageStats?.total_uploads || 0} uploaded documents,
              including their summaries, warnings, and analysis. This action cannot be undone.
            </p>
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3 mb-6">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                💡 Government documents from official sources will not be affected.
              </p>
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => setShowClearUploadsConfirm(false)}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900
                         dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                onClick={() => clearUploadsMutation.mutate()}
                disabled={clearUploadsMutation.isPending}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg
                         disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {clearUploadsMutation.isPending ? 'Clearing...' : 'Clear All Uploads'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper function to get readable file type names
function getFileTypeName(mimeType: string): string {
  if (!mimeType) return 'Unknown'

  if (mimeType.includes('pdf')) return '📄 PDF'
  if (mimeType.includes('word') || mimeType.includes('document')) return '📝 Word Document'
  if (mimeType.includes('text')) return '📋 Text File'
  if (mimeType.includes('html')) return '🌐 HTML'

  return mimeType
}
