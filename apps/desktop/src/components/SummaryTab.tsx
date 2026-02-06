import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import CitationChip from './CitationChip'
import ConfidencePanel from './ConfidencePanel'
import { LoadingSkeleton } from './LoadingSkeleton'

interface Citation {
  doc_id: string
  version_id: string
  text: string
  quote_text?: string
  verified: boolean
  match_method: string
  confidence: number
  confidence_reasons?: string[]
  location: {
    section?: string
    page?: number
    char_start?: number
    char_end?: number
  }
}

interface SummaryTabProps {
  versionId: string
  docId: string
  onJumpToCitation: (citation: Citation) => void
}

export default function SummaryTab({ versionId, docId, onJumpToCitation }: SummaryTabProps) {
  const { data: summaryData, isLoading, error } = useQuery({
    queryKey: ['summary', versionId],
    queryFn: () =>
      api.post('/api/summary/summarize', {
        version_id: versionId,
        focus: 'general',
        max_length: 'medium',
      }),
    enabled: !!versionId,
    staleTime: 10 * 60 * 1000, // 10 minutes - summaries don't change often
    cacheTime: 60 * 60 * 1000, // 1 hour
    keepPreviousData: true,
  })

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <h3 className="font-semibold text-red-800 dark:text-red-200 mb-2">
          Error Generating Summary
        </h3>
        <p className="text-sm text-red-700 dark:text-red-300">
          {error instanceof Error ? error.message : 'Failed to generate summary'}
        </p>
      </div>
    )
  }

  if (!summaryData?.summary) {
    return null
  }

  const { summary } = summaryData
  const grounding = summary.grounding

  return (
    <div className="space-y-6">
      {/* Legal Disclaimer - Always visible */}
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">⚠️</span>
          <div>
            <h3 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-1">
              Important: Not Legal Advice
            </h3>
            <p className="text-sm text-yellow-700 dark:text-yellow-300">
              {summary.disclaimer || 'This summary is for educational purposes only and is not legal advice. Consult a qualified attorney for legal advice specific to your situation.'}
            </p>
          </div>
        </div>
      </div>

      {/* Upload Settings Display - Show configuration used for analysis */}
      {summaryData.upload_settings && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
            Analysis Configuration
          </h3>
          <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
            This analysis was generated based on the following settings you selected during upload:
          </p>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-blue-600 dark:text-blue-400 font-medium">Document Type:</span>
              <p className="text-blue-800 dark:text-blue-200">{summaryData.upload_settings.doc_type || 'Not specified'}</p>
            </div>
            <div>
              <span className="text-blue-600 dark:text-blue-400 font-medium">Focus Area:</span>
              <p className="text-blue-800 dark:text-blue-200">{summaryData.upload_settings.focus || 'General'}</p>
            </div>
            {summaryData.upload_settings.jurisdiction && (
              <div>
                <span className="text-blue-600 dark:text-blue-400 font-medium">Jurisdiction:</span>
                <p className="text-blue-800 dark:text-blue-200">{summaryData.upload_settings.jurisdiction}</p>
              </div>
            )}
            {summaryData.upload_settings.upload_date && (
              <div>
                <span className="text-blue-600 dark:text-blue-400 font-medium">Uploaded:</span>
                <p className="text-blue-800 dark:text-blue-200">
                  {new Date(summaryData.upload_settings.upload_date).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Low Confidence Banner */}
      {grounding && grounding.confidence < 0.5 && (
        <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <h3 className="font-semibold text-orange-800 dark:text-orange-200 mb-1">
                Low Confidence Analysis
              </h3>
              <p className="text-sm text-orange-700 dark:text-orange-300">
                The analysis confidence is below 50%. Please carefully review the cited text in the original document
                to verify accuracy. Some citations may not have been verified in the extracted text.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Confidence Panel */}
      {grounding && (
        <ConfidencePanel
          confidence={grounding.confidence}
          confidenceReasons={grounding.confidence_reasons || []}
          verifiedCount={grounding.verified_count || 0}
          totalCount={grounding.citation_count || 0}
          exactMatches={grounding.exact_matches || 0}
          fuzzyMatches={grounding.fuzzy_matches || 0}
        />
      )}

      {/* Summary Sections */}
      <div className="space-y-4">
        {summary.summary_sections?.map((section: any, idx: number) => (
          <div key={idx} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              {section.heading}
            </h3>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              {section.content}
            </p>
            {/* Render Citations from API (grounding.citations) */}
            {summaryData.summary?.citations && summaryData.summary.citations.length > 0 && (
              <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  📚 Sources ({summaryData.summary.citations.length}):
                </p>
                <div className="flex flex-wrap gap-2">
                  {summaryData.summary.citations.slice(0, 10).map((citation: Citation, cidx: number) => (
                    <CitationChip
                      key={cidx}
                      citation={citation}
                      index={cidx}
                      onJumpToCitation={onJumpToCitation}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Coverage Information */}
      {summary.coverage && (
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Coverage Details
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Text Length:</span>
              <p className="font-medium text-gray-900 dark:text-white">
                {summary.coverage.text_length?.toLocaleString()} chars
              </p>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Sections:</span>
              <p className="font-medium text-gray-900 dark:text-white">
                {summary.coverage.sections_analyzed}
              </p>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Warnings:</span>
              <p className="font-medium text-gray-900 dark:text-white">
                {summary.coverage.warnings_detected}
              </p>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Full Text:</span>
              <p className="font-medium text-gray-900 dark:text-white">
                {summary.coverage.full_text_analyzed ? 'Yes' : 'No'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
