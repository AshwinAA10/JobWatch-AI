import React, { useEffect, useState } from 'react'
import { Search, X } from 'lucide-react'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  debounceMs?: number
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  placeholder = 'Search by job title, skill, or keyword...',
  debounceMs = 350,
}) => {
  const [innerValue, setInnerValue] = useState<string>(value)

  useEffect(() => {
    setInnerValue(value)
  }, [value])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (innerValue !== value) {
        onChange(innerValue)
      }
    }, debounceMs)

    return () => clearTimeout(timer)
  }, [innerValue, debounceMs, onChange, value])

  const handleClear = () => {
    setInnerValue('')
    onChange('')
  }

  return (
    <div className="search-bar-wrapper">
      <Search size={18} className="search-icon" aria-hidden="true" />
      <input
        type="search"
        className="search-input"
        placeholder={placeholder}
        value={innerValue}
        onChange={(e) => setInnerValue(e.target.value)}
        aria-label="Search job postings"
      />
      {innerValue && (
        <button
          type="button"
          className="search-clear-btn"
          onClick={handleClear}
          aria-label="Clear search query"
        >
          <X size={16} />
        </button>
      )}
    </div>
  )
}
