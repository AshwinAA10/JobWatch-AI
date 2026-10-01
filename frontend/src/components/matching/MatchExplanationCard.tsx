import { CheckCircle, AlertTriangle } from 'lucide-react'

interface MatchExplanationCardProps {
  reasons?: string[]
  matchedCriteria?: string[]
  missingCriteria?: string[]
}

export const MatchExplanationCard: React.FC<MatchExplanationCardProps> = ({
  reasons = [],
  matchedCriteria = [],
  missingCriteria = [],
}) => {
  const hasReasons = reasons && reasons.length > 0
  const hasMatched = matchedCriteria && matchedCriteria.length > 0
  const hasMissing = missingCriteria && missingCriteria.length > 0

  if (!hasReasons && !hasMatched && !hasMissing) {
    return (
      <div className="card match-explanation-card">
        <h4 className="card-title">Match Explanation</h4>
        <p className="text-muted text-sm">
          No detailed matching explanation has been computed for this job opening.
        </p>
      </div>
    )
  }

  return (
    <div className="card match-explanation-card">
      <div className="card-header-clean">
        <h4 className="card-title">Why This Job Matches You</h4>
        <span className="card-subtitle-badge">Match Intelligence</span>
      </div>

      {/* Primary reasons / highlights */}
      {hasReasons && (
        <div className="explanation-section">
          <h5 className="explanation-subhead">Key Alignment Factors</h5>
          <ul className="explanation-list">
            {reasons.map((reason, idx) => (
              <li key={`reason-${idx}`} className="explanation-item match-positive">
                <CheckCircle size={16} className="item-icon icon-positive" aria-hidden="true" />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Matched criteria */}
      {hasMatched && (
        <div className="explanation-section">
          <h5 className="explanation-subhead">Matched Requirements</h5>
          <div className="tags-flex">
            {matchedCriteria.map((crit, idx) => (
              <span key={`matched-${idx}`} className="badge badge-success">
                ✓ {crit}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Missing criteria */}
      {hasMissing && (
        <div className="explanation-section">
          <h5 className="explanation-subhead">Gaps or Unmet Criteria</h5>
          <ul className="explanation-list">
            {missingCriteria.map((gap, idx) => (
              <li key={`missing-${idx}`} className="explanation-item match-neutral">
                <AlertTriangle size={16} className="item-icon icon-warning" aria-hidden="true" />
                <span>{gap}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
