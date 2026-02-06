import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useState, useRef, useMemo } from 'react'
import { api } from '../lib/api'
import SummaryTab from '../components/SummaryTab'
import WarningsTab from '../components/WarningsTab'
import QuestionsTab from '../components/QuestionsTab'
import PowerImbalancesTab from '../components/PowerImbalancesTab'

type TabType = 'metadata' | 'content' | 'summary' | 'warnings' | 'questions' | 'power-imbalances'

interface Citation {
  doc_id: string
  version_id: string
  text: string
  quote_text?: string
  verified: boolean
  match_method: string
  confidence: number
  location: {
    section?: string
    page?: number
    char_start?: number
    char_end?: number
  }
}

export default function DocumentViewer() {
  const { id } = useParams<{ id: string }>()
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('metadata')
  const [highlightedCitation, setHighlightedCitation] = useState<Citation | null>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['document', id],
    queryFn: () => api.get(`/api/docs/${id}`),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
  })

  const { data: versionData } = useQuery({
    queryKey: ['version', selectedVersionId],
    queryFn: () => api.get(`/api/docs/versions/${selectedVersionId}`),
    enabled: !!selectedVersionId,
    staleTime: 5 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
    keepPreviousData: true, // Prevent flash when switching versions
  })

  // Handler for jumping to citation
  const handleJumpToCitation = (citation: Citation) => {
    // Switch to content tab
    setActiveTab('content')
    // Set highlighted citation
    setHighlightedCitation(citation)
    // Scroll after a small delay to ensure tab switch completes
    setTimeout(() => {
      const element = document.getElementById(`citation-${citation.location.char_start}`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 100)
  }

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="text-gray-600 dark:text-gray-400">Loading document...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-8">
        <div className="text-red-600">Document not found</div>
      </div>
    )
  }

  const doc = data.document
  const versions = data.versions || []

  // Auto-select first version if none selected
  if (versions.length > 0 && !selectedVersionId) {
    setSelectedVersionId(versions[0].id)
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          {doc.title}
        </h1>
        <div className="flex gap-4 text-sm text-gray-600 dark:text-gray-400">
          <span>{doc.doc_type}</span>
          {doc.jurisdiction && (
            <>
              <span>•</span>
              <span>{doc.jurisdiction}</span>
            </>
          )}
          {doc.canonical_url && (
            <>
              <span>•</span>
              <a
                href={doc.canonical_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                View Source
              </a>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex gap-4 overflow-x-auto">
          {/* Show Summary/Warnings/Questions tabs only for user uploads */}
          {doc.is_user_uploaded ? (
            <>
              <TabButton
                active={activeTab === 'summary'}
                onClick={() => setActiveTab('summary')}
                icon="📄"
                label="Summary"
              />
              <TabButton
                active={activeTab === 'warnings'}
                onClick={() => setActiveTab('warnings')}
                icon="⚠️"
                label="Warnings"
              />
              <TabButton
                active={activeTab === 'questions'}
                onClick={() => setActiveTab('questions')}
                icon="❓"
                label="Questions"
              />
              <TabButton
                active={activeTab === 'power-imbalances'}
                onClick={() => setActiveTab('power-imbalances')}
                icon="⚖️"
                label="Power Imbalances"
              />
              <TabButton
                active={activeTab === 'content'}
                onClick={() => setActiveTab('content')}
                icon="📝"
                label="Full Text"
              />
              <TabButton
                active={activeTab === 'metadata'}
                onClick={() => setActiveTab('metadata')}
                icon="ℹ️"
                label="Metadata"
              />
            </>
          ) : (
            <>
              <TabButton
                active={activeTab === 'metadata'}
                onClick={() => setActiveTab('metadata')}
                label="Metadata"
              />
              <TabButton
                active={activeTab === 'content'}
                onClick={() => setActiveTab('content')}
                label="Content"
              />
            </>
          )}
        </div>
      </div>

      {/* Content Area */}
      {activeTab === 'metadata' && (
        <div className="space-y-6">
          {/* Document Metadata */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Document Information
            </h2>
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-600 dark:text-gray-400">Source</dt>
                <dd className="text-gray-900 dark:text-white font-medium capitalize">
                  {doc.source_id?.replace('_', ' ')}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600 dark:text-gray-400">Type</dt>
                <dd className="text-gray-900 dark:text-white font-medium capitalize">
                  {doc.doc_type?.replace('_', ' ')}
                </dd>
              </div>
              {doc.jurisdiction && (
                <div>
                  <dt className="text-sm text-gray-600 dark:text-gray-400">Jurisdiction</dt>
                  <dd className="text-gray-900 dark:text-white font-medium">
                    {doc.jurisdiction}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Versions */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Versions ({versions.length})
            </h2>
            <div className="space-y-3">
              {versions.map((version: any) => (
                <div
                  key={version.id}
                  onClick={() => {
                    setSelectedVersionId(version.id)
                    setActiveTab('content')
                  }}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedVersionId === version.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {version.version_label}
                    </span>
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {version.content_mode}
                    </span>
                  </div>
                  {version.published_ts && (
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Published: {new Date(version.published_ts).toLocaleDateString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'content' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6" ref={contentRef}>
          {versionData ? (
            <div>
              <div className="mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {versionData.title}
                </h2>
                {versionData.effective_date && (
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Effective: {new Date(versionData.effective_date).toLocaleDateString()}
                  </div>
                )}
              </div>

              <div className="prose dark:prose-invert max-w-none">
                <HighlightedText
                  text={versionData.normalized_text || 'No content available'}
                  highlightedCitation={highlightedCitation}
                />
              </div>
            </div>
          ) : (
            <div className="text-gray-600 dark:text-gray-400">
              Select a version to view its content
            </div>
          )}
        </div>
      )}

      {/* Summary Tab */}
      {activeTab === 'summary' && selectedVersionId && (
        <SummaryTab
          versionId={selectedVersionId}
          docId={id || ''}
          onJumpToCitation={handleJumpToCitation}
        />
      )}

      {/* Warnings Tab */}
      {activeTab === 'warnings' && selectedVersionId && (
        <WarningsTab
          versionId={selectedVersionId}
          onJumpToCitation={handleJumpToCitation}
        />
      )}

      {/* Questions Tab */}
      {activeTab === 'questions' && selectedVersionId && (
        <QuestionsTab versionId={selectedVersionId} />
      )}

      {/* Power Imbalances Tab */}
      {activeTab === 'power-imbalances' && selectedVersionId && (
        <PowerImbalancesTab versionId={selectedVersionId} />
      )}
    </div>
  )
}

// Highlighted Text Component
function HighlightedText({
  text,
  highlightedCitation,
}: {
  text: string
  highlightedCitation: Citation | null
}) {
  const rendered = useMemo(() => {
    if (!highlightedCitation || !highlightedCitation.location.char_start || !highlightedCitation.location.char_end) {
      return <pre className="whitespace-pre-wrap text-gray-900 dark:text-gray-100 font-sans">{text}</pre>
    }

    const start = highlightedCitation.location.char_start
    const end = highlightedCitation.location.char_end

    const before = text.substring(0, start)
    const highlighted = text.substring(start, end)
    const after = text.substring(end)

    return (
      <pre className="whitespace-pre-wrap text-gray-900 dark:text-gray-100 font-sans">
        {before}
        <mark
          id={`citation-${start}`}
          className="bg-yellow-200 dark:bg-yellow-700 px-1 rounded animate-pulse"
          style={{ animationIterationCount: 3 }}
        >
          {highlighted}
        </mark>
        {after}
      </pre>
    )
  }, [text, highlightedCitation])

  return rendered
}

// Tab Button Component
function TabButton({
  active,
  onClick,
  label,
  icon,
}: {
  active: boolean
  onClick: () => void
  label: string
  icon?: string
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 border-b-2 font-medium transition-colors whitespace-nowrap flex items-center gap-2 ${
        active
          ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
          : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
      }`}
    >
      {icon && <span>{icon}</span>}
      {label}
    </button>
  )
}
