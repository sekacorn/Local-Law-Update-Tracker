import { useState } from 'react'

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

interface CitationChipProps {
  citation: Citation
  index: number
  onJumpToCitation: (citation: Citation) => void
}

export default function CitationChip({ citation, index, onJumpToCitation }: CitationChipProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  const isLowConfidence = citation.confidence < 0.5
  const isUnverified = !citation.verified

  // Choose chip color based on verification status
  const chipColor = isUnverified
    ? 'bg-red-100 hover:bg-red-200 text-red-800 border-red-300'
    : isLowConfidence
    ? 'bg-yellow-100 hover:bg-yellow-200 text-yellow-800 border-yellow-300'
    : 'bg-blue-100 hover:bg-blue-200 text-blue-800 border-blue-300'

  const locationText = citation.location.section
    ? citation.location.section
    : citation.location.page
    ? `Page ${citation.location.page}`
    : `Chars ${citation.location.char_start}-${citation.location.char_end}`

  return (
    <div className="relative inline-block">
      <button
        onClick={() => onJumpToCitation(citation)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${chipColor}`}
      >
        <span className="text-lg leading-none">
          {isUnverified ? '⚠️' : '📌'}
        </span>
        <span>{locationText}</span>
        {citation.match_method === 'fuzzy' && (
          <span className="text-xs opacity-75" title="Fuzzy match">≈</span>
        )}
      </button>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64">
          <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg p-3 shadow-lg">
            {isUnverified && (
              <div className="mb-2 pb-2 border-b border-gray-700 dark:border-gray-300">
                <p className="font-semibold text-red-300 dark:text-red-700">
                  ⚠️ Could not verify quote in extracted text
                </p>
              </div>
            )}

            <div className="space-y-1.5">
              <div>
                <span className="font-semibold">Confidence:</span>{' '}
                {(citation.confidence * 100).toFixed(0)}%
              </div>

              {citation.location.section && (
                <div>
                  <span className="font-semibold">Section:</span>{' '}
                  {citation.location.section}
                </div>
              )}

              {citation.location.page && (
                <div>
                  <span className="font-semibold">Page:</span>{' '}
                  {citation.location.page}
                </div>
              )}

              <div>
                <span className="font-semibold">Match:</span>{' '}
                {citation.match_method === 'exact' ? 'Exact' : citation.match_method === 'fuzzy' ? 'Fuzzy (~85%)' : 'None'}
              </div>

              {citation.quote_text && (
                <div className="mt-2 pt-2 border-t border-gray-700 dark:border-gray-300">
                  <p className="italic opacity-90 line-clamp-3">
                    "{citation.quote_text.substring(0, 100)}..."
                  </p>
                </div>
              )}
            </div>

            {/* Arrow */}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2">
              <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900 dark:border-t-gray-100"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
