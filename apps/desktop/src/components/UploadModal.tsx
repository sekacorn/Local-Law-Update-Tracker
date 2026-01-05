import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
}

interface UploadMetadata {
  title: string
  jurisdiction: string
  doc_type: string
  focus: string
}

interface UploadResponse {
  doc_id: string
  version_id: string
  stats: {
    file_size: number
    format: string
    sections: number
    words: number
    confidence: number
    pages?: number
  }
  warnings: string[]
}

const SUPPORTED_FORMATS = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'text/html': ['.html'],
}

const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB

export default function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const queryClient = useQueryClient()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [metadata, setMetadata] = useState<UploadMetadata>({
    title: '',
    jurisdiction: '',
    doc_type: '',
    focus: 'general',
  })
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)

  const uploadMutation = useMutation({
    mutationFn: async ({ file, metadata }: { file: File; metadata: UploadMetadata }) => {
      return api.uploadFile('/api/uploads', file, metadata) as Promise<UploadResponse>
    },
    onSuccess: (data) => {
      setUploadResult(data)
      queryClient.invalidateQueries({ queryKey: ['db-status'] })
      queryClient.invalidateQueries({ queryKey: ['recent-uploads'] })
    },
  })

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      setSelectedFile(file)
      // Auto-populate title from filename
      if (!metadata.title) {
        const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '')
        setMetadata(prev => ({ ...prev, title: nameWithoutExt }))
      }
    }
  }, [metadata.title])

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: SUPPORTED_FORMATS,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return

    uploadMutation.mutate({
      file: selectedFile,
      metadata,
    })
  }

  const handleClose = () => {
    setSelectedFile(null)
    setMetadata({
      title: '',
      jurisdiction: '',
      doc_type: '',
      focus: 'general',
    })
    setUploadResult(null)
    uploadMutation.reset()
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Upload Document
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {uploadResult ? (
            // Success view
            <div className="space-y-4">
              <div className="flex items-center justify-center text-green-500 mb-4">
                <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <h3 className="text-xl font-semibold text-gray-900 dark:text-white text-center">
                Upload Successful!
              </h3>

              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-2">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Format:</span>
                    <p className="font-medium text-gray-900 dark:text-white">{uploadResult.stats.format.toUpperCase()}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Size:</span>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {(uploadResult.stats.file_size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Sections:</span>
                    <p className="font-medium text-gray-900 dark:text-white">{uploadResult.stats.sections}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Words:</span>
                    <p className="font-medium text-gray-900 dark:text-white">{uploadResult.stats.words}</p>
                  </div>
                  {uploadResult.stats.pages && (
                    <div>
                      <span className="text-sm text-gray-600 dark:text-gray-400">Pages:</span>
                      <p className="font-medium text-gray-900 dark:text-white">{uploadResult.stats.pages}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Confidence:</span>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {(uploadResult.stats.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </div>

              {uploadResult.warnings.length > 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                  <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-2">Warnings:</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-yellow-700 dark:text-yellow-300">
                    {uploadResult.warnings.map((warning, idx) => (
                      <li key={idx}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              <button
                onClick={handleClose}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Done
              </button>
            </div>
          ) : (
            // Upload form
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Drag & Drop Zone */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                }`}
              >
                <input {...getInputProps()} />
                {selectedFile ? (
                  <div className="space-y-2">
                    <svg className="w-12 h-12 mx-auto text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-lg font-medium text-gray-900 dark:text-white">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedFile(null)
                      }}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <svg className="w-12 h-12 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-gray-700 dark:text-gray-300">
                      {isDragActive ? 'Drop the file here' : 'Drag & drop a file here, or click to select'}
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports: PDF, DOCX, TXT, HTML (max 50MB)
                    </p>
                  </div>
                )}
              </div>

              {fileRejections.length > 0 && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                  <p className="text-sm text-red-700 dark:text-red-300">
                    {fileRejections[0].errors[0].message}
                  </p>
                </div>
              )}

              {/* Metadata Form */}
              {selectedFile && (
                <div className="space-y-4">
                  {/* Important Notice Banner */}
                  <div className="bg-amber-50 dark:bg-amber-900/20 border-2 border-amber-400 dark:border-amber-600 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <svg className="w-6 h-6 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <div className="flex-1">
                        <h4 className="font-bold text-amber-900 dark:text-amber-200 mb-1">
                          Important: Document Type and Focus Area
                        </h4>
                        <p className="text-sm text-amber-800 dark:text-amber-300 mb-2">
                          The analysis you receive will be tailored based on the <strong>Document Type</strong> and <strong>Focus Area</strong> you select below. Choose carefully to get the most relevant advice.
                        </p>
                        <ul className="text-sm text-amber-800 dark:text-amber-300 space-y-1 list-disc list-inside">
                          <li><strong>Lease:</strong> Identifies rental terms, obligations, and tenant rights</li>
                          <li><strong>Employment:</strong> Highlights work conditions, compensation, and termination clauses</li>
                          <li><strong>HR Document:</strong> Focuses on policies, procedures, and employee rights</li>
                          <li><strong>Terms of Service/Privacy Policy:</strong> Analyzes data rights, power imbalances, and liabilities</li>
                          <li><strong>Contract:</strong> General contract analysis for agreements and obligations</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Document Title
                    </label>
                    <input
                      type="text"
                      value={metadata.title}
                      onChange={(e) => setMetadata(prev => ({ ...prev, title: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Employment Agreement"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Jurisdiction
                      </label>
                      <select
                        value={metadata.jurisdiction}
                        onChange={(e) => setMetadata(prev => ({ ...prev, jurisdiction: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select...</option>
                        <option value="Federal">Federal</option>
                        <option value="State">State</option>
                        <option value="Local">Local</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Document Type
                      </label>
                      <select
                        value={metadata.doc_type}
                        onChange={(e) => setMetadata(prev => ({ ...prev, doc_type: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select...</option>
                        <option value="Lease">Lease</option>
                        <option value="Contract">Contract</option>
                        <option value="HR">HR Document</option>
                        <option value="Employment">Employment Agreement</option>
                        <option value="Terms of Service">Terms of Service</option>
                        <option value="Privacy Policy">Privacy Policy</option>
                        <option value="User Agreement">User Agreement</option>
                        <option value="EULA">End User License Agreement (EULA)</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Focus Area
                    </label>
                    <select
                      value={metadata.focus}
                      onChange={(e) => setMetadata(prev => ({ ...prev, focus: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="general">General</option>
                      <option value="home_buying">Home Buying</option>
                      <option value="job_hr">Job & HR</option>
                      <option value="lease">Lease</option>
                      <option value="privacy">Privacy & Data Rights</option>
                      <option value="consumer">Consumer Rights</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Error Display */}
              {uploadMutation.isError && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <p className="text-sm text-red-700 dark:text-red-300">
                    {uploadMutation.error instanceof Error ? uploadMutation.error.message : 'Upload failed'}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  disabled={uploadMutation.isPending}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!selectedFile || uploadMutation.isPending}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
