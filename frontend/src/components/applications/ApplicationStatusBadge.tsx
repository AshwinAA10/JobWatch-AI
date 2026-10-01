import React from 'react'
import {
  Clock,
  Search,
  Calendar,
  Award,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react'
import { ApplicationStatus } from '../../types/application'

interface ApplicationStatusBadgeProps {
  status: ApplicationStatus | string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export const ApplicationStatusBadge: React.FC<ApplicationStatusBadgeProps> = ({
  status,
  size = 'md',
  className = '',
}) => {
  const normStatus = (status || '').toUpperCase()

  const getStatusConfig = () => {
    switch (normStatus) {
      case 'APPLIED':
        return {
          label: 'Applied',
          icon: <Clock size={size === 'sm' ? 12 : 14} />,
          bgClass: 'badge-applied',
        }
      case 'SCREENING':
        return {
          label: 'Screening',
          icon: <Search size={size === 'sm' ? 12 : 14} />,
          bgClass: 'badge-screening',
        }
      case 'INTERVIEW':
        return {
          label: 'Interview',
          icon: <Calendar size={size === 'sm' ? 12 : 14} />,
          bgClass: 'badge-interview',
        }
      case 'OFFER':
        return {
          label: 'Offer Received',
          icon: <Award size={size === 'sm' ? 12 : 14} />,
          bgClass: 'badge-offer',
        }
      case 'ACCEPTED':
        return {
          label: 'Accepted',
          icon: <CheckCircle2 size={size === 'sm' ? 12 : 14} />,
          bgClass: 'badge-accepted',
        }
      case 'REJECTED':
        return {
          label: 'Rejected',
          icon: <XCircle size={size === 'sm' ? 12 : 14} />,
          bgClass: 'badge-rejected',
        }
      case 'WITHDRAWN':
        return {
          label: 'Withdrawn',
          icon: <AlertCircle size={size === 'sm' ? 12 : 14} />,
          bgClass: 'badge-withdrawn',
        }
      default:
        return {
          label: status,
          icon: <Clock size={size === 'sm' ? 12 : 14} />,
          bgClass: 'badge-default',
        }
    }
  }

  const { label, icon, bgClass } = getStatusConfig()

  return (
    <span
      className={`app-status-badge app-status-${size} ${bgClass} ${className}`}
      role="status"
      aria-label={`Application status: ${label}`}
    >
      <span className="badge-icon" aria-hidden="true">
        {icon}
      </span>
      <span className="badge-text">{label}</span>
    </span>
  )
}
