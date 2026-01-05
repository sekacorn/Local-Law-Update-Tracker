import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

interface SummaryTabProps {
  versionId: string
  docId: string
}

export default function SummaryTab({ versionId, docId }: SummaryTabProps) {
  const { data: summaryData, isLoading, error } = useQuery({
    queryKey: ['summary', versionId],
    queryFn: () =>
      api.post('/api/summary/summarize', {
        version_id: versionId,
        focus: 'general',
        max_length: 'medium',
      }),
    enabled: !!versionId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-600 dark:text-gray-400">Generating summary...</div>
      </div>
    )
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

      {/* Confidence Meter */}
      {grounding && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
            Analysis Confidence
          </h3>
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      grounding.confidence >= 0.8
                        ? 'bg-green-500'
                        : grounding.confidence >= 0.5
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${grounding.confidence * 100}%` }}
                  />
                </div>
              </div>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 w-16 text-right">
                {(grounding.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {grounding.can_cite ? (
                <span className="text-green-600 dark:text-green-400">✓ Citations available</span>
              ) : (
                <span className="text-red-600 dark:text-red-400">⚠ Limited citation support</span>
              )}
              {' • '}
              {grounding.citation_count} citation{grounding.citation_count !== 1 ? 's' : ''} extracted
            </div>
          </div>
        </div>
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
            {section.citations && section.citations.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <details className="text-sm">
                  <summary className="cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
                    View citations ({section.citations.length})
                  </summary>
                  <div className="mt-2 space-y-2">
                    {section.citations.map((cite: any, cidx: number) => (
                      <div key={cidx} className="text-gray-600 dark:text-gray-400 text-xs">
                        Chars {cite.start}-{cite.end}
                      </div>
                    ))}
                  </div>
                </details>
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
