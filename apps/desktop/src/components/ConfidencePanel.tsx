import { useState } from 'react'

interface ConfidencePanelProps {
  confidence: number
  confidenceReasons?: string[]
  verifiedCount?: number
  totalCount?: number
  exactMatches?: number
  fuzzyMatches?: number
}

export default function ConfidencePanel({
  confidence,
  confidenceReasons = [],
  verifiedCount = 0,
  totalCount = 0,
  exactMatches = 0,
  fuzzyMatches = 0,
}: ConfidencePanelProps) {
  const [showReasons, setShowReasons] = useState(false)

  const confidencePercent = Math.round(confidence * 100)
  const isLow = confidence < 0.5
  const isMedium = confidence >= 0.5 && confidence < 0.8
  const isHigh = confidence >= 0.8

  const barColor = isHigh
    ? 'bg-green-500'
    : isMedium
    ? 'bg-yellow-500'
    : 'bg-red-500'

  const textColor = isHigh
    ? 'text-green-700 dark:text-green-400'
    : isMedium
    ? 'text-yellow-700 dark:text-yellow-400'
    : 'text-red-700 dark:text-red-400'

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        <span>🎯</span>
        Analysis Confidence
      </h3>

      {/* Confidence Bar */}
      <div className="space-y-3">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${barColor}`}
                style={{ width: `${confidencePercent}%` }}
              />
            </div>
          </div>
          <span className={`text-lg font-bold w-16 text-right ${textColor}`}>
            {confidencePercent}%
          </span>
        </div>

        {/* Stats Row */}
        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center gap-1.5">
            {verifiedCount === totalCount ? (
              <span className="text-green-600 dark:text-green-400">✓</span>
            ) : (
              <span className="text-yellow-600 dark:text-yellow-400">⚠</span>
            )}
            <span>
              {verifiedCount}/{totalCount} verified
            </span>
          </div>

          {exactMatches > 0 && (
            <div className="flex items-center gap-1.5">
              <span>•</span>
              <span>{exactMatches} exact</span>
            </div>
          )}

          {fuzzyMatches > 0 && (
            <div className="flex items-center gap-1.5">
              <span>•</span>
              <span>{fuzzyMatches} fuzzy</span>
            </div>
          )}
        </div>

        {/* Expandable Reasons */}
        {confidenceReasons.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setShowReasons(!showReasons)}
              className="flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
            >
              <svg
                className={`w-4 h-4 transition-transform ${showReasons ? 'rotate-90' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
              {showReasons ? 'Hide' : 'Show'} confidence factors
            </button>

            {showReasons && (
              <div className="mt-3 space-y-1.5">
                {confidenceReasons.map((reason, idx) => (
                  <div
                    key={idx}
                    className={`text-xs p-2 rounded ${
                      reason.startsWith('WARNING')
                        ? 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200'
                        : 'bg-gray-50 dark:bg-gray-900 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {reason.startsWith('WARNING') ? (
                      <span className="flex items-start gap-1.5">
                        <span className="text-sm">⚠️</span>
                        <span>{reason.replace('WARNING: ', '')}</span>
                      </span>
                    ) : (
                      <span className="flex items-start gap-1.5">
                        <span className="text-sm">✓</span>
                        <span>{reason}</span>
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
