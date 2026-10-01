import React from 'react'
import { Sparkles, CheckCircle2, AlertCircle } from 'lucide-react'

interface MatchScoreBadgeProps {
  score?: number | null
  confidence?: string | null
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

export const MatchScoreBadge: React.FC<MatchScoreBadgeProps> = ({
  score,
  confidence,
  size = 'md',
  showLabel = true,
}) => {
  if (score === null || score === undefined) {
    return (
      <span className={`match-badge match-unscored match-badge-${size}`} title="Not scored yet">
        <span className="match-badge-text">Unscored</span>
      </span>
    )
  }

  // Format percentage rounded to integer
  const scorePercent = Math.round(score)

  let tierClass = 'match-high'
  let label = 'Strong Fit'
  let Icon = Sparkles

  if (scorePercent >= 80) {
    tierClass = 'match-high'
    label = 'Strong Fit'
    Icon = Sparkles
  } else if (scorePercent >= 60) {
    tierClass = 'match-medium'
    label = 'Moderate Fit'
    Icon = CheckCircle2
  } else {
    tierClass = 'match-low'
    label = 'Low Fit'
    Icon = AlertCircle
  }

  return (
    <div
      className={`match-badge-container ${tierClass} match-badge-${size}`}
      role="status"
      aria-label={`Match score: ${scorePercent} percent, ${label}`}
    >
      <div className="match-badge-pill">
        <Icon size={size === 'sm' ? 12 : size === 'lg' ? 18 : 14} className="match-badge-icon" />
        <span className="match-badge-score">{scorePercent}%</span>
      </div>
      {showLabel && (
        <span className="match-badge-label">
          {confidence ? `${label} (${confidence.toLowerCase()})` : label}
        </span>
      )}
    </div>
  )
}
