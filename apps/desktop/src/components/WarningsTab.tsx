import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

interface WarningsTabProps {
  versionId: string
}

const RISK_COLORS = {
  high: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    text: 'text-red-800 dark:text-red-200',
    badge: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
  },
  medium: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    text: 'text-yellow-800 dark:text-yellow-200',
    badge: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
  },
  low: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-800 dark:text-blue-200',
    badge: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
  },
}

const CATEGORY_ICONS = {
  liability: '⚖️',
  deadline: '⏰',
  penalty: '💰',
  waiver: '✋',
  termination: '🔚',
  arbitration: '🤝',
  class_action: '👥',
  confidentiality: '🤐',
}

export default function WarningsTab({ versionId }: WarningsTabProps) {
  const { data: summaryData, isLoading } = useQuery({
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
        <div className="text-gray-600 dark:text-gray-400">Analyzing for warnings...</div>
      </div>
    )
  }

  const warnings = summaryData?.summary?.warnings || []

  if (warnings.length === 0) {
    return (
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-8 text-center">
        <div className="text-4xl mb-3">✅</div>
        <h3 className="text-lg font-semibold text-green-800 dark:text-green-200 mb-2">
          No Major Warnings Detected
        </h3>
        <p className="text-green-700 dark:text-green-300">
          This document appears to have no significant liability or risk clauses. However, you should still review it carefully with a professional.
        </p>
      </div>
    )
  }

  // Group warnings by risk level
  const groupedWarnings = warnings.reduce((acc: any, warning: any) => {
    const level = warning.risk_level || 'medium'
    if (!acc[level]) acc[level] = []
    acc[level].push(warning)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      {/* Overall Warning Banner */}
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">⚠️</span>
          <div>
            <h3 className="font-semibold text-red-800 dark:text-red-200 mb-1">
              {warnings.length} Warning{warnings.length !== 1 ? 's' : ''} Detected
            </h3>
            <p className="text-sm text-red-700 dark:text-red-300">
              This document contains clauses that may affect your rights or obligations. Review these carefully and consider consulting an attorney.
            </p>
          </div>
        </div>
      </div>

      {/* High Risk Warnings */}
      {groupedWarnings.high && groupedWarnings.high.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 flex items-center gap-2">
            <span>🔴</span>
            High Risk ({groupedWarnings.high.length})
          </h3>
          {groupedWarnings.high.map((warning: any, idx: number) => (
            <WarningCard key={idx} warning={warning} riskLevel="high" />
          ))}
        </div>
      )}

      {/* Medium Risk Warnings */}
      {groupedWarnings.medium && groupedWarnings.medium.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 flex items-center gap-2">
            <span>🟡</span>
            Medium Risk ({groupedWarnings.medium.length})
          </h3>
          {groupedWarnings.medium.map((warning: any, idx: number) => (
            <WarningCard key={idx} warning={warning} riskLevel="medium" />
          ))}
        </div>
      )}

      {/* Low Risk Warnings */}
      {groupedWarnings.low && groupedWarnings.low.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200 flex items-center gap-2">
            <span>🔵</span>
            Low Risk ({groupedWarnings.low.length})
          </h3>
          {groupedWarnings.low.map((warning: any, idx: number) => (
            <WarningCard key={idx} warning={warning} riskLevel="low" />
          ))}
        </div>
      )}

      {/* Recommendation */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
          💡 Recommendation
        </h3>
        <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
          Before signing or agreeing to this document:
        </p>
        <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-2 list-disc list-inside">
          <li>Carefully review all warnings above</li>
          <li>Understand what rights you may be giving up</li>
          <li>Consider consulting with a qualified attorney</li>
          <li>Ask questions about anything unclear</li>
          <li>Negotiate terms if possible</li>
        </ul>
      </div>
    </div>
  )
}

function WarningCard({ warning, riskLevel }: { warning: any; riskLevel: string }) {
  const colors = RISK_COLORS[riskLevel as keyof typeof RISK_COLORS] || RISK_COLORS.medium
  const icon = CATEGORY_ICONS[warning.category as keyof typeof CATEGORY_ICONS] || '📋'

  return (
    <div className={`${colors.bg} ${colors.border} border rounded-lg p-4`}>
      <div className="flex items-start gap-3 mb-3">
        <span className="text-2xl">{icon}</span>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h4 className={`font-semibold ${colors.text} capitalize`}>
              {warning.category.replace('_', ' ')}
            </h4>
            <span className={`px-2 py-1 rounded text-xs font-medium ${colors.badge}`}>
              {warning.who_affected || 'You'}
            </span>
          </div>
          <p className={`text-sm ${colors.text} mb-3`}>{warning.description}</p>

          {/* Citation */}
          {warning.citation_text && (
            <details className="text-sm">
              <summary className={`cursor-pointer ${colors.text} font-medium hover:underline`}>
                View clause text
              </summary>
              <div className="mt-2 p-3 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                <p className="text-gray-700 dark:text-gray-300 italic text-xs">
                  "{warning.citation_text}"
                </p>
                {warning.citation_context && (
                  <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-gray-600 dark:text-gray-400 text-xs">
                      Context: {warning.citation_context}
                    </p>
                  </div>
                )}
              </div>
            </details>
          )}
        </div>
      </div>
    </div>
  )
}
