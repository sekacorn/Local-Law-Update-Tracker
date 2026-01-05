import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

interface PowerImbalancesTabProps {
  versionId: string
}

export default function PowerImbalancesTab({ versionId }: PowerImbalancesTabProps) {
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set())

  const { data: summaryData, isLoading, error } = useQuery({
    queryKey: ['summary', versionId],
    queryFn: () =>
      api.post('/api/summary/summarize', {
        version_id: versionId,
        focus: 'privacy',  // Use privacy focus to trigger policy analysis
        max_length: 'medium',
      }),
    enabled: !!versionId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-600 dark:text-gray-400">Analyzing power dynamics...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <h3 className="font-semibold text-red-800 dark:text-red-200 mb-2">
          Error Analyzing Document
        </h3>
        <p className="text-sm text-red-700 dark:text-red-300">
          {error instanceof Error ? error.message : 'Failed to analyze power imbalances'}
        </p>
      </div>
    )
  }

  const summary = summaryData?.summary

  if (!summary?.power_imbalances) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        No power imbalance analysis available for this document.
      </div>
    )
  }

  const { power_imbalances, data_rights, consumer_red_flags, key_takeaways } = summary

  const toggleItem = (index: number) => {
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedItems(newExpanded)
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200'
      case 'medium':
        return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200'
      default:
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200'
    }
  }

  const getControlColor = (control: string) => {
    switch (control) {
      case 'none':
        return 'text-red-600 dark:text-red-400'
      case 'limited':
        return 'text-yellow-600 dark:text-yellow-400'
      case 'full':
        return 'text-green-600 dark:text-green-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Key Takeaways */}
      {key_takeaways && key_takeaways.length > 0 && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-amber-900 dark:text-amber-100 mb-3">
            Key Takeaways
          </h3>
          <ul className="space-y-2">
            {key_takeaways.map((takeaway: string, idx: number) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-amber-800 dark:text-amber-200">
                <span className="text-amber-600 dark:text-amber-400 mt-0.5">•</span>
                <span>{takeaway}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Power Imbalances Summary */}
      {power_imbalances && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Power Imbalances ({power_imbalances.total})
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
            <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                {power_imbalances.high_severity}
              </div>
              <div className="text-sm text-red-800 dark:text-red-200">High Severity</div>
            </div>
            <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                {power_imbalances.medium_severity}
              </div>
              <div className="text-sm text-yellow-800 dark:text-yellow-200">Medium Severity</div>
            </div>
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {power_imbalances.total}
              </div>
              <div className="text-sm text-blue-800 dark:text-blue-200">Total Found</div>
            </div>
          </div>

          {/* Individual Power Imbalances */}
          <div className="space-y-3">
            {power_imbalances.items && power_imbalances.items.map((item: any, idx: number) => (
              <div
                key={idx}
                className={`border rounded-lg p-4 ${getSeverityColor(item.severity)}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-semibold text-sm mb-1">
                      {item.category.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                    </h4>
                    <p className="text-sm">{item.description}</p>
                  </div>
                  <span className="ml-2 px-2 py-1 text-xs font-medium rounded">
                    {item.severity.toUpperCase()}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 mt-3 text-sm">
                  <div>
                    <div className="font-medium mb-1">Company Can:</div>
                    <div className="text-xs opacity-90">{item.company_power}</div>
                  </div>
                  <div>
                    <div className="font-medium mb-1">You Can:</div>
                    <div className="text-xs opacity-90">{item.user_power}</div>
                  </div>
                </div>

                {item.citation && (
                  <div className="mt-3 pt-3 border-t border-current border-opacity-20">
                    <button
                      onClick={() => toggleItem(idx)}
                      className="text-xs font-medium hover:underline"
                    >
                      {expandedItems.has(idx) ? 'Hide' : 'Show'} clause
                    </button>
                    {expandedItems.has(idx) && (
                      <div className="mt-2 p-2 bg-white dark:bg-gray-900 bg-opacity-50 rounded text-xs">
                        "{item.citation.text}"
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Rights */}
      {data_rights && data_rights.total_issues > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Data Rights & Privacy ({data_rights.total_issues} issues)
          </h3>

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                {data_rights.no_control}
              </div>
              <div className="text-sm text-red-800 dark:text-red-200">No Control</div>
            </div>
            <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                {data_rights.limited_control}
              </div>
              <div className="text-sm text-yellow-800 dark:text-yellow-200">Limited Control</div>
            </div>
            <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {data_rights.total_issues - data_rights.no_control - data_rights.limited_control}
              </div>
              <div className="text-sm text-green-800 dark:text-green-200">Full Control</div>
            </div>
          </div>

          <div className="space-y-2">
            {data_rights.items && data_rights.items.map((item: any, idx: number) => (
              <div
                key={idx}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-3"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-sm text-gray-900 dark:text-white capitalize">
                    {item.type.replace(/_/g, ' ')}
                  </h4>
                  <span className={`text-xs font-medium ${getControlColor(item.user_control)}`}>
                    {item.user_control.toUpperCase()} CONTROL
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">{item.description}</p>

                {item.citation && (
                  <details className="mt-2 text-xs">
                    <summary className="cursor-pointer text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">
                      View clause
                    </summary>
                    <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-900 rounded">
                      "{item.citation.text}"
                    </div>
                  </details>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Consumer Red Flags */}
      {consumer_red_flags && consumer_red_flags.total > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Consumer Protection Concerns ({consumer_red_flags.total})
          </h3>
          <div className="space-y-2">
            {consumer_red_flags.items && consumer_red_flags.items.map((item: any, idx: number) => (
              <div
                key={idx}
                className="border border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3"
              >
                <h4 className="font-medium text-sm text-orange-900 dark:text-orange-100 mb-1 capitalize">
                  {item.type.replace(/_/g, ' ')}
                </h4>
                <p className="text-xs text-orange-800 dark:text-orange-200">"{item.text}"</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Legal Disclaimer */}
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
        <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
          Important: Not Legal Advice
        </h4>
        <p className="text-sm text-yellow-700 dark:text-yellow-300">
          {summary.disclaimer || 'This analysis is for educational purposes only and is not legal advice. The power imbalances and risks identified are based on automated text analysis. Consult a qualified attorney for legal advice specific to your situation.'}
        </p>
      </div>
    </div>
  )
}
