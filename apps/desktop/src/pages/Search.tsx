import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

export default function Search() {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [docTypeFilter, setDocTypeFilter] = useState<string>('')

  // Fetch all uploaded documents
  const { data: uploads } = useQuery({
    queryKey: ['all-uploads'],
    queryFn: async () => {
      const docs = await api.get('/api/uploads/list')
      return docs
    },
  })

  const { data, isLoading } = useQuery({
    queryKey: ['search', submittedQuery, sourceFilter, docTypeFilter],
    queryFn: () => {
      const params = new URLSearchParams({ q: submittedQuery })
      if (sourceFilter) params.append('source_id', sourceFilter)
      if (docTypeFilter) params.append('doc_type', docTypeFilter)
      return api.get(`/api/search?${params.toString()}`)
    },
    enabled: submittedQuery.length > 0,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmittedQuery(query)
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
        Search Documents
      </h1>

      {/* Uploaded Documents Section */}
      {uploads && uploads.documents && uploads.documents.length > 0 && (
        <div className="mb-8 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Your Uploaded Documents ({uploads.documents.length})
          </h2>
          <div className="space-y-3">
            {uploads.documents.slice(0, 5).map((doc: any) => (
              <Link
                key={doc.id}
                to={`/document/${doc.id}`}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors border border-gray-200 dark:border-gray-600"
              >
                <div className="flex items-center gap-3 flex-1">
                  <span className="text-2xl">{getFileIcon(doc.upload_mime)}</span>
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {doc.title}
                    </h3>
                    <div className="flex gap-3 text-xs text-gray-500 dark:text-gray-400 mt-1">
                      <span>{doc.original_filename}</span>
                      <span>•</span>
                      <span className="capitalize">{doc.doc_type || 'Unknown type'}</span>
                      {doc.first_seen_ts && (
                        <>
                          <span>•</span>
                          <span>Uploaded {new Date(doc.first_seen_ts).toLocaleDateString()}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            ))}
            {uploads.documents.length > 5 && (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center pt-2">
                Showing 5 of {uploads.documents.length} uploads
              </p>
            )}
          </div>
        </div>
      )}

      {/* Search Form */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for legal documents..."
            className="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={query.trim().length === 0}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg
                     font-medium disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
          >
            Search
          </button>
        </div>
      </form>

      {/* Filters */}
      <div className="mb-8 flex gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Source
          </label>
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Sources</option>
            <option value="user_uploads">📁 User Uploads</option>
            <option value="federal_register">Federal Register</option>
            <option value="state_codes">State Codes</option>
            <option value="local_ordinances">Local Ordinances</option>
          </select>
        </div>

        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Document Type
          </label>
          <select
            value={docTypeFilter}
            onChange={(e) => setDocTypeFilter(e.target.value)}
            className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Types</option>
            <option value="regulation">Regulation</option>
            <option value="statute">Statute</option>
            <option value="ordinance">Ordinance</option>
            <option value="lease">Lease</option>
            <option value="contract">Contract</option>
            <option value="agreement">Agreement</option>
            <option value="policy">Policy</option>
            <option value="other">Other</option>
          </select>
        </div>

        {(sourceFilter || docTypeFilter) && (
          <div className="flex items-end">
            <button
              onClick={() => {
                setSourceFilter('')
                setDocTypeFilter('')
              }}
              className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>

      {/* Results */}
      {isLoading && (
        <div className="text-gray-600 dark:text-gray-400">Searching...</div>
      )}

      {data && (
        <div>
          <div className="mb-4 text-gray-600 dark:text-gray-400">
            Found {data.total} results for "{submittedQuery}"
          </div>

          <div className="space-y-4">
            {data.results.map((result: any) => (
              <Link
                key={result.version_id}
                to={`/document/${result.document_id}`}
                className="block bg-white dark:bg-gray-800 rounded-lg shadow p-6
                         hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    {result.is_user_uploaded && getFileIcon(result.upload_mime)}
                    {result.title}
                  </h3>
                  {result.is_user_uploaded && (
                    <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs font-medium rounded-full">
                      📁 Upload
                    </span>
                  )}
                </div>

                <div className="flex gap-4 text-sm text-gray-600 dark:text-gray-400 mb-3 flex-wrap">
                  {result.is_user_uploaded && result.original_filename && (
                    <>
                      <span className="font-medium">{result.original_filename}</span>
                      <span>•</span>
                    </>
                  )}
                  {!result.is_user_uploaded && (
                    <>
                      <span>{result.source_name}</span>
                      <span>•</span>
                    </>
                  )}
                  <span className="capitalize">{result.doc_type?.replace('_', ' ')}</span>
                  {result.published_ts && (
                    <>
                      <span>•</span>
                      <span>{new Date(result.published_ts).toLocaleDateString()}</span>
                    </>
                  )}
                  {result.is_user_uploaded && result.confidence_score != null && (
                    <>
                      <span>•</span>
                      <span className={`font-medium ${getConfidenceColor(result.confidence_score)}`}>
                        {Math.round(result.confidence_score * 100)}% confidence
                      </span>
                    </>
                  )}
                </div>

                {result.snippet && (
                  <div
                    className="text-gray-700 dark:text-gray-300 text-sm"
                    dangerouslySetInnerHTML={{ __html: result.snippet }}
                  />
                )}
              </Link>
            ))}
          </div>

          {data.results.length === 0 && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              No results found. Try a different search query.
            </div>
          )}
        </div>
      )}

      {!submittedQuery && !isLoading && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          Enter a search query to find documents
        </div>
      )}
    </div>
  )
}

// Helper function to get file type icon
function getFileIcon(mimeType: string): string {
  if (!mimeType) return '📄'

  if (mimeType.includes('pdf')) return '📄'
  if (mimeType.includes('word') || mimeType.includes('document')) return '📝'
  if (mimeType.includes('text')) return '📋'
  if (mimeType.includes('html')) return '🌐'

  return '📄'
}

// Helper function to get confidence color
function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'text-green-600 dark:text-green-400'
  if (confidence >= 0.5) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}
