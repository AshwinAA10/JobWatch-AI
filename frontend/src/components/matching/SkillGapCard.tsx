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
    <div className="card skill-gap-card" style={{ marginTop: '1rem', padding: '1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <Sparkles size={18} color="#2563eb" />
        <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>Skill Gap & Transferability</h4>
      </div>

      {isLoading && <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>Analyzing skill ontology...</p>}

      {error && <p style={{ fontSize: '0.875rem', color: '#ef4444' }}>Unable to load skill gap analysis.</p>}

      {data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.875rem' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
              <span style={{ fontWeight: 500 }}>Requirement Coverage</span>
              <span style={{ fontWeight: 600, color: '#2563eb' }}>{Math.round(data.required_coverage * 100)}%</span>
            </div>
            <div style={{ width: '100%', height: '6px', background: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${Math.min(100, Math.round(data.required_coverage * 100))}%`,
                  height: '100%',
                  background: '#2563eb',
                  borderRadius: '4px',
                }}
              />
            </div>
          </div>

          {/* Transferable Skills Highlight */}
          {data.transferable_matches && data.transferable_matches.length > 0 && (
            <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', padding: '0.75rem' }}>
              <span style={{ fontWeight: 600, color: '#166534', display: 'block', marginBottom: '0.25rem' }}>
                Transferable Skills Detected:
              </span>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#15803d' }}>
                {data.transferable_matches.map((item: any, idx: number) => (
                  <li key={idx} style={{ marginBottom: '0.2rem' }}>
                    <strong>{item.matched_via}</strong> <ArrowRight size={12} style={{ display: 'inline', margin: '0 2px' }} /> fulfills <strong>{item.target_skill}</strong> ({Math.round(item.transfer_weight * 100)}% transfer)
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Skills */}
          {data.missing_required && data.missing_required.length > 0 && (
            <div>
              <span style={{ color: '#b91c1c', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <AlertCircle size={14} /> Missing Required Skills:
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.35rem' }}>
                {data.missing_required.map((skill: string, idx: number) => (
                  <span
                    key={idx}
                    style={{
                      background: '#fee2e2',
                      color: '#991b1b',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 500,
                    }}
                  >
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
