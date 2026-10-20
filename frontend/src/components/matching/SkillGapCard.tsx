import React, { useEffect, useState } from 'react'
import { Sparkles, ArrowRight, AlertCircle } from 'lucide-react'
import { fetchSkillGaps } from '../../services/jobs'

interface SkillGapCardProps {
  jobId: string
  token: string | null
}

export const SkillGapCard: React.FC<SkillGapCardProps> = ({ jobId, token }) => {
  const [data, setData] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !jobId) return

    let isMounted = true
    setIsLoading(true)
    setError(null)

    fetchSkillGaps(jobId, token)
      .then((res) => {
        if (isMounted) setData(res)
      })
      .catch((err) => {
        if (isMounted) setError(err.message)
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [jobId, token])

  if (!token || (!data && !isLoading && !error)) return null

  return (
    <div className="card skill-gap-card">
      <div className="skill-gap-header">
        <Sparkles size={16} className="text-accent" />
        <h4 className="skill-gap-title">Skill Gap & Transferability</h4>
      </div>

      {isLoading && <p className="text-muted text-sm">Analyzing skill ontology...</p>}

      {error && <p className="text-danger text-sm">Unable to load skill gap analysis.</p>}

      {data && (
        <div className="skill-gap-body">
          <div className="skill-gap-coverage-section">
            <div className="flex-between mb-1">
              <span className="coverage-label">Requirement Coverage</span>
              <span className="coverage-val text-accent text-strong">
                {Math.round(data.required_coverage * 100)}%
              </span>
            </div>
            <div
              className="progress-track"
              role="progressbar"
              aria-valuenow={Math.round(data.required_coverage * 100)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Requirement Coverage"
            >
              <div
                className="progress-fill bg-accent"
                style={{ width: `${Math.min(100, Math.round(data.required_coverage * 100))}%` }}
              />
            </div>
          </div>

          {/* Transferable Skills Highlight */}
          {data.transferable_matches && data.transferable_matches.length > 0 && (
            <div className="transferable-skills-banner">
              <span className="transferable-badge-title">
                Transferable Skills Detected:
              </span>
              <ul className="transferable-list">
                {data.transferable_matches.map((item: any, idx: number) => (
                  <li key={idx} className="transferable-item">
                    <span className="skill-source">{item.matched_via}</span>
                    <ArrowRight size={11} className="icon-transfer" />
                    <span className="skill-target">{item.target_skill}</span>
                    <span className="transfer-weight">({Math.round(item.transfer_weight * 100)}% transfer)</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Skills */}
          {data.missing_required && data.missing_required.length > 0 && (
            <div className="missing-skills-section">
              <span className="missing-skills-title">
                <AlertCircle size={13} className="icon-mr text-danger" /> Missing Required Skills:
              </span>
              <div className="missing-tags-flex">
                {data.missing_required.map((skill: string, idx: number) => (
                  <span key={idx} className="badge badge-missing">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

