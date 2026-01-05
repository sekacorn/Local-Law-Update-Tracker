import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import UploadModal from '../components/UploadModal'

export default function Dashboard() {
  const [showUploadModal, setShowUploadModal] = useState(false)

  const { data: status, isLoading } = useQuery({
    queryKey: ['db-status'],
    queryFn: () => api.get('/api/db/status'),
  })

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get('/health'),
  })

  const { data: recentUploads } = useQuery({
    queryKey: ['recent-uploads'],
    queryFn: () => api.get('/api/uploads/recent?limit=5'),
  })

  if (isLoading) {
    return <div className="p-8">Loading...</div>
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <button
          onClick={() => setShowUploadModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Upload Document
        </button>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatusCard
          title="Documents"
          value={status?.counts?.documents || 0}
          icon="📄"
        />
        <StatusCard
          title="Versions"
          value={status?.counts?.versions || 0}
          icon="📝"
        />
        <StatusCard
          title="Changes"
          value={status?.counts?.changes || 0}
          icon="🔄"
        />
      </div>

      {/* Storage Info */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Storage
        </h2>
        <div className="space-y-3">
          <StorageRow
            label="Database"
            size={status?.database?.size_bytes || 0}
          />
          <StorageRow
            label="Cache"
            size={status?.cache?.size_bytes || 0}
            files={status?.cache?.files || 0}
          />
        </div>
      </div>

      {/* Recent Uploads */}
      {recentUploads?.uploads && recentUploads.uploads.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Recent Uploads
          </h2>
          <div className="space-y-3">
            {recentUploads.uploads.map((upload: any) => (
              <div
                key={upload.id}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="text-2xl">
                    {upload.upload_mime === 'pdf' ? '📄' : upload.upload_mime === 'docx' ? '📝' : '📋'}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {upload.title}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {upload.original_filename} • {upload.doc_type || 'Document'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {new Date(upload.first_seen_ts).toLocaleDateString()}
                  </div>
                  {upload.latest_confidence && (
                    <div className="text-xs text-gray-400">
                      {(upload.latest_confidence * 100).toFixed(0)}% confidence
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* System Status */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          System Status
        </h2>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Backend</span>
            <span className={`font-medium ${
              health?.status === 'ok' ? 'text-green-600' : 'text-red-600'
            }`}>
              {health?.status || 'Unknown'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Database</span>
            <span className={`font-medium ${
              health?.database === 'ok' ? 'text-green-600' : 'text-red-600'
            }`}>
              {health?.database || 'Unknown'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600 dark:text-gray-400">Storage Mode</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {health?.storage_mode || 'full'}
            </span>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      <UploadModal isOpen={showUploadModal} onClose={() => setShowUploadModal(false)} />
    </div>
  )
}

function StatusCard({ title, value, icon }: { title: string; value: number; icon: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {value.toLocaleString()}
          </p>
        </div>
        <span className="text-4xl">{icon}</span>
      </div>
    </div>
  )
}

function StorageRow({ label, size, files }: { label: string; size: number; files?: number }) {
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-600 dark:text-gray-400">{label}</span>
      <div className="text-right">
        <span className="text-gray-900 dark:text-white font-medium">
          {formatBytes(size)}
        </span>
        {files !== undefined && (
          <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
            ({files} files)
          </span>
        )}
      </div>
    </div>
  )
}
