import React from 'react'
import { Sparkles, Check, AlertCircle, Lightbulb } from 'lucide-react'
import { AIExplanationData } from '../../types/job'

interface AIInsightsCardProps {
  aiExplanation?: AIExplanationData | null
  deterministicFallback?: {
    reasons?: string[]
    matchedCriteria?: string[]
  }
}

export const AIInsightsCard: React.FC<AIInsightsCardProps> = ({
  aiExplanation,
  deterministicFallback,
}) => {
  // If AI explanation is present
  if (aiExplanation && (aiExplanation.summary || aiExplanation.recommendation)) {
    return (
      <div className="card ai-insights-card">
        <div className="ai-insights-header">
          <div className="ai-badge-chip">
            <Sparkles size={14} className="ai-icon" />
            <span>AI-Assisted Insights</span>
          </div>
          <span className="text-xs text-muted">Semantic Analysis</span>
        </div>

        {aiExplanation.summary && (
          <div className="ai-section">
            <p className="ai-summary-text">{aiExplanation.summary}</p>
          </div>
        )}

        <div className="ai-grid">
          {aiExplanation.strengths && aiExplanation.strengths.length > 0 && (
            <div className="ai-col">
              <h5 className="ai-col-title text-success">
                <Check size={14} className="icon-mr" />
                Key Candidate Strengths
              </h5>
              <ul className="ai-bullet-list">
                {aiExplanation.strengths.map((str, idx) => (
                  <li key={`str-${idx}`}>{str}</li>
                ))}
              </ul>
            </div>
          )}

          {aiExplanation.gaps && aiExplanation.gaps.length > 0 && (
            <div className="ai-col">
              <h5 className="ai-col-title text-warning">
                <AlertCircle size={14} className="icon-mr" />
                Growth Areas & Gaps
              </h5>
              <ul className="ai-bullet-list">
                {aiExplanation.gaps.map((gap, idx) => (
                  <li key={`gap-${idx}`}>{gap}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {aiExplanation.recommendation && (
          <div className="ai-recommendation-box">
            <Lightbulb size={16} className="ai-rec-icon" />
            <div>
              <span className="ai-rec-label">Advisory Recommendation: </span>
              <span className="ai-rec-text">{aiExplanation.recommendation}</span>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Graceful deterministic fallback
  const reasons = deterministicFallback?.reasons || []
  if (reasons.length > 0) {
    return (
      <div className="card ai-insights-fallback-card">
        <div className="card-header-clean">
          <h4 className="card-title">Deterministic Match Reasoning</h4>
          <span className="card-subtitle-badge">Authoritative Engine</span>
        </div>
        <p className="text-muted text-sm">
          AI semantic evaluation is currently queued or in baseline mode. Showing rule-based alignment:
        </p>
        <ul className="explanation-list mt-2">
          {reasons.slice(0, 3).map((r, i) => (
            <li key={i} className="explanation-item match-positive">
              <Check size={15} className="item-icon icon-positive" />
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return null
}
