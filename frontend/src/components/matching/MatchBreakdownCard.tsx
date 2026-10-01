import React from 'react'

interface MatchBreakdownCardProps {
  breakdown?: Record<string, number | any> | null
}

const CATEGORY_LABELS: Record<string, string> = {
  skills: 'Skills Match',
  experience: 'Experience Level',
  education: 'Education Requirement',
  location: 'Location Fit',
  workplace: 'Workplace Preference',
  employment_type: 'Employment Type',
  salary: 'Compensation Fit',
  semantic_fit: 'Semantic Fit',
}

export const MatchBreakdownCard: React.FC<MatchBreakdownCardProps> = ({ breakdown }) => {
  if (!breakdown || Object.keys(breakdown).length === 0) {
    return (
      <div className="card match-breakdown-card">
        <h4 className="card-title">Match Breakdown</h4>
        <p className="text-muted text-sm">Detailed category breakdown is not available for this evaluation.</p>
      </div>
    )
  }

  // Filter numeric entries
  const entries = Object.entries(breakdown).filter(([key, value]) => {
    // Only numeric or score fields
    return typeof value === 'number' && key !== 'total_score' && key !== 'overall'
  })

  if (entries.length === 0) {
    return null
  }

  return (
    <div className="card match-breakdown-card">
      <div className="card-header-clean">
        <h4 className="card-title">Score Breakdown</h4>
        <span className="card-subtitle-badge">Deterministic Dimensions</span>
      </div>

      <div className="breakdown-list">
        {entries.map(([key, val]) => {
          const numVal = Math.min(100, Math.max(0, Math.round(val as number)))
          const label = CATEGORY_LABELS[key] || key.replace(/_/g, ' ')

          let barColor = 'bg-accent'
          if (numVal >= 80) barColor = 'bar-high'
          else if (numVal >= 60) barColor = 'bar-medium'
          else barColor = 'bar-low'

          return (
            <div key={key} className="breakdown-row">
              <div className="breakdown-labels">
                <span className="breakdown-name">{label}</span>
                <span className="breakdown-val">{numVal}%</span>
              </div>
              <div
                className="progress-track"
                role="progressbar"
                aria-valuenow={numVal}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={label}
              >
                <div
                  className={`progress-fill ${barColor}`}
                  style={{ width: `${numVal}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
