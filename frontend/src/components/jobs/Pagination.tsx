import React from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  currentPage: number
  totalPages: number
  totalItems: number
  pageSize: number
  onPageChange: (page: number) => void
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
}) => {
  if (totalPages <= 1) return null

  const startItem = (currentPage - 1) * pageSize + 1
  const endItem = Math.min(currentPage * pageSize, totalItems)

  return (
    <nav className="pagination-nav" aria-label="Pagination">
      <div className="pagination-summary">
        Showing <span className="text-strong">{startItem}</span> to{' '}
        <span className="text-strong">{endItem}</span> of{' '}
        <span className="text-strong">{totalItems}</span> jobs
      </div>

      <div className="pagination-controls">
        <button
          type="button"
          className="btn btn-secondary btn-sm pagination-btn"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          aria-label="Previous page"
        >
          <ChevronLeft size={16} />
          <span>Prev</span>
        </button>

        <span className="pagination-current-page" aria-current="page">
          Page {currentPage} of {totalPages}
        </span>

        <button
          type="button"
          className="btn btn-secondary btn-sm pagination-btn"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          aria-label="Next page"
        >
          <span>Next</span>
          <ChevronRight size={16} />
        </button>
      </div>
    </nav>
  )
}
