import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useState } from 'react'

interface QuestionsTabProps {
  versionId: string
}

export default function QuestionsTab({ versionId }: QuestionsTabProps) {
  const [checkedQuestions, setCheckedQuestions] = useState<Set<number>>(new Set())

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

  const toggleQuestion = (idx: number) => {
    const newChecked = new Set(checkedQuestions)
    if (newChecked.has(idx)) {
      newChecked.delete(idx)
    } else {
      newChecked.add(idx)
    }
    setCheckedQuestions(newChecked)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-600 dark:text-gray-400">Generating questions...</div>
      </div>
    )
  }

  const questions = summaryData?.summary?.questions_for_professional || []

  if (questions.length === 0) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-8 text-center">
        <div className="text-4xl mb-3">❓</div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          No Questions Generated
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          We couldn't generate specific questions for this document. Consider consulting a professional for a thorough review.
        </p>
      </div>
    )
  }

  const completionPercentage = (checkedQuestions.size / questions.length) * 100

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">💼</span>
          <div className="flex-1">
            <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-1">
              Questions to Ask a Professional
            </h3>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              Use this checklist when consulting with a lawyer or legal professional about this document.
            </p>
          </div>
        </div>
      </div>

      {/* Progress Tracker */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-gray-900 dark:text-white">Your Progress</h4>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {checkedQuestions.size} / {questions.length} asked
          </span>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 dark:bg-blue-500 transition-all duration-300"
            style={{ width: `${completionPercentage}%` }}
          />
        </div>
      </div>

      {/* Questions Checklist */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Question Checklist
        </h3>
        <div className="space-y-3">
          {questions.map((question: string, idx: number) => (
            <label
              key={idx}
              className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                checkedQuestions.has(idx)
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
              }`}
            >
              <input
                type="checkbox"
                checked={checkedQuestions.has(idx)}
                onChange={() => toggleQuestion(idx)}
                className="mt-1 h-5 w-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex-1">
                <p className={`${
                  checkedQuestions.has(idx)
                    ? 'text-gray-500 dark:text-gray-400 line-through'
                    : 'text-gray-900 dark:text-white'
                }`}>
                  {question}
                </p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Tips */}
      <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-6">
        <h3 className="font-semibold text-purple-800 dark:text-purple-200 mb-3">
          💡 Tips for Your Consultation
        </h3>
        <ul className="text-sm text-purple-700 dark:text-purple-300 space-y-2">
          <li className="flex items-start gap-2">
            <span className="mt-0.5">•</span>
            <span>Bring a copy of this document to your consultation</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-0.5">•</span>
            <span>Take notes on the answers you receive</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-0.5">•</span>
            <span>Ask for clarification if you don't understand something</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-0.5">•</span>
            <span>Discuss any concerns or red flags that stood out to you</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-0.5">•</span>
            <span>Ask about potential negotiation points or alternatives</span>
          </li>
        </ul>
      </div>

      {/* Print/Export */}
      <div className="flex gap-3">
        <button
          onClick={() => window.print()}
          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          Print Questions
        </button>
        <button
          onClick={() => {
            const text = questions.map((q: string, i: number) => `${i + 1}. ${q}`).join('\n\n')
            navigator.clipboard.writeText(text)
            alert('Questions copied to clipboard!')
          }}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
          </svg>
          Copy to Clipboard
        </button>
      </div>
    </div>
  )
}
