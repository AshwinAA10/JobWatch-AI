import React from 'react'

interface LoadingSkeletonProps {
  count?: number
  type?: 'card' | 'line' | 'detail'
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  count = 3,
  type = 'card',
}) => {
  return (
    <div className="skeleton-wrapper" aria-busy="true" aria-label="Loading content">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className={`skeleton-item skeleton-${type}`}>
          <div className="skeleton-shimmer" />
        </div>
      ))}
    </div>
  )
}
