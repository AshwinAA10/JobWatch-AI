import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import { ApplicationStatusBadge } from '../components/applications/ApplicationStatusBadge'
import { ApplicationTimeline } from '../components/applications/ApplicationTimeline'
import { ApplicationNotesCard } from '../components/applications/ApplicationNotesCard'
import { InterviewCard } from '../components/applications/InterviewCard'
import { JobCard } from '../components/jobs/JobCard'
import { AuthProvider } from '../context/AuthContext'
import { ApplicationHistoryItem, ApplicationNoteItem, InterviewItem } from '../types/application'
import { JobCard as JobCardType } from '../types/job'

describe('ApplicationStatusBadge Component', () => {
  it('renders correctly for various lifecycle statuses', () => {
    const { rerender } = render(<ApplicationStatusBadge status="APPLIED" />)
    expect(screen.getByText('Applied')).toBeInTheDocument()

    rerender(<ApplicationStatusBadge status="INTERVIEW" />)
    expect(screen.getByText('Interview')).toBeInTheDocument()

    rerender(<ApplicationStatusBadge status="OFFER" />)
    expect(screen.getByText('Offer Received')).toBeInTheDocument()

    rerender(<ApplicationStatusBadge status="REJECTED" />)
    expect(screen.getByText('Rejected')).toBeInTheDocument()

    rerender(<ApplicationStatusBadge status="ACCEPTED" />)
    expect(screen.getByText('Accepted')).toBeInTheDocument()
  })

  it('provides accessible role and aria-label', () => {
    render(<ApplicationStatusBadge status="SCREENING" />)
    const badge = screen.getByRole('status')
    expect(badge).toHaveAttribute('aria-label', 'Application status: Screening')
  })
})

describe('ApplicationTimeline Component', () => {
  const mockHistory: ApplicationHistoryItem[] = [
    {
      id: 'h1',
      application_id: 'app1',
      old_status: null,
      new_status: 'APPLIED',
      changed_at: '2026-10-01T10:00:00Z',
      note: 'Initial application submitted',
      created_at: '2026-10-01T10:00:00Z',
    },
    {
      id: 'h2',
      application_id: 'app1',
      old_status: 'APPLIED',
      new_status: 'SCREENING',
      changed_at: '2026-10-05T14:30:00Z',
      note: 'Recruiter phone screening scheduled',
      created_at: '2026-10-05T14:30:00Z',
    },
    {
      id: 'h3',
      application_id: 'app1',
      old_status: 'SCREENING',
      new_status: 'INTERVIEW',
      changed_at: '2026-10-12T09:00:00Z',
      note: 'Passed screen, invited to system design round',
      created_at: '2026-10-12T09:00:00Z',
    },
  ]

  it('renders timeline events chronologically with status transitions and notes', () => {
    render(<ApplicationTimeline history={mockHistory} />)

    expect(screen.getByText('Applied')).toBeInTheDocument()
    expect(screen.getByText('Screening')).toBeInTheDocument()
    expect(screen.getByText('Interview')).toBeInTheDocument()

    expect(screen.getByText('"Initial application submitted"')).toBeInTheDocument()
    expect(screen.getByText('"Recruiter phone screening scheduled"')).toBeInTheDocument()
    expect(screen.getByText('"Passed screen, invited to system design round"')).toBeInTheDocument()
  })

  it('renders empty message when no events exist', () => {
    render(<ApplicationTimeline history={[]} />)
    expect(screen.getByText('No timeline events recorded yet.')).toBeInTheDocument()
  })
})

describe('ApplicationNotesCard Component', () => {
  const mockNotes: ApplicationNoteItem[] = [
    {
      id: 'n1',
      application_id: 'app1',
      content: 'Follow up with recruiter on Friday about team placement.',
      created_at: '2026-10-02T10:00:00Z',
      updated_at: '2026-10-02T10:00:00Z',
    },
  ]

  it('renders private notes list and submits new note', async () => {
    const handleAdd = vi.fn().mockResolvedValue(undefined)
    const handleDelete = vi.fn().mockResolvedValue(undefined)

    render(
      <ApplicationNotesCard
        notes={mockNotes}
        onAddNote={handleAdd}
        onDeleteNote={handleDelete}
      />,
    )

    expect(
      screen.getByText('Follow up with recruiter on Friday about team placement.'),
    ).toBeInTheDocument()

    const input = screen.getByPlaceholderText(/Add recruiter details/i)
    fireEvent.change(input, { target: { value: 'New note about compensation band' } })

    const submitBtn = screen.getByRole('button', { name: /Add Note/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(handleAdd).toHaveBeenCalledWith('New note about compensation band')
    })
  })
})

describe('InterviewCard Component', () => {
  const mockInterview: InterviewItem = {
    id: 'int-1',
    application_id: 'app-1',
    interview_type: 'TECHNICAL',
    status: 'SCHEDULED',
    scheduled_at: '2026-10-20T15:00:00Z',
    duration_minutes: 60,
    interviewer_names: 'Dr. Jane Hopper, Lead AI Architect',
    location: 'Google Meet',
    meeting_url: 'https://meet.google.com/xyz-uvwx-rst',
    notes: 'Focus on distributed consensus and high-throughput messaging.',
    created_at: '2026-10-02T12:00:00Z',
    updated_at: '2026-10-02T12:00:00Z',
  }

  it('renders interview details with secure meeting link', () => {
    const handleStatus = vi.fn().mockResolvedValue(undefined)
    const handleDelete = vi.fn().mockResolvedValue(undefined)

    render(
      <InterviewCard
        interview={mockInterview}
        onStatusChange={handleStatus}
        onDelete={handleDelete}
      />,
    )

    expect(screen.getByText('TECHNICAL')).toBeInTheDocument()
    expect(screen.getByText(/60 minutes/i)).toBeInTheDocument()
    expect(screen.getByText('Dr. Jane Hopper, Lead AI Architect')).toBeInTheDocument()
    expect(screen.getByText('Google Meet')).toBeInTheDocument()

    const meetingLink = screen.getByRole('link', { name: /Join Meeting Link/i })
    expect(meetingLink).toHaveAttribute('href', 'https://meet.google.com/xyz-uvwx-rst')
    expect(meetingLink).toHaveAttribute('target', '_blank')
    expect(meetingLink).toHaveAttribute('rel', 'noopener noreferrer')
  })
})

describe('JobCard Application Integration', () => {
  it('renders applied badge when job has application_id', () => {
    const appliedJob: JobCardType = {
      id: 'job-1',
      company_id: 'co-1',
      company_name: 'Datadog',
      company_slug: 'datadog',
      title: 'Senior Site Reliability Engineer',
      first_seen_at: '2026-09-15T00:00:00Z',
      is_active: true,
      is_saved: false,
      application_id: 'app-12345',
      application_status: 'INTERVIEW',
    }

    render(
      <AuthProvider>
        <BrowserRouter>
          <JobCard job={appliedJob} />
        </BrowserRouter>
      </AuthProvider>,
    )

    expect(screen.getByText(/Applied \(INTERVIEW\)/i)).toBeInTheDocument()
    const appLink = screen.getByRole('link', { name: /Applied \(INTERVIEW\)/i })
    expect(appLink).toHaveAttribute('href', '/applications/app-12345')
  })
})
