import React, { useState } from 'react'
import { Plus, Trash2, StickyNote, AlertCircle, Loader2 } from 'lucide-react'
import { ApplicationNoteItem } from '../../types/application'

interface ApplicationNotesCardProps {
  notes: ApplicationNoteItem[]
  onAddNote: (content: string) => Promise<void>
  onDeleteNote: (noteId: string) => Promise<void>
  className?: string
}

export const ApplicationNotesCard: React.FC<ApplicationNotesCardProps> = ({
  notes,
  onAddNote,
  onDeleteNote,
  className = '',
}) => {
  const [newContent, setNewContent] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newContent.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      await onAddNote(newContent.trim())
      setNewContent('')
    } catch (err: any) {
      setError(err.message || 'Failed to save note.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (noteId: string) => {
    if (!window.confirm('Are you sure you want to delete this note?')) return

    setDeletingId(noteId)
    setError(null)
    try {
      await onDeleteNote(noteId)
    } catch (err: any) {
      setError(err.message || 'Failed to delete note.')
    } finally {
      setDeletingId(null)
    }
  }

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString)
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return isoString
    }
  }

  return (
    <div className={`app-notes-card card ${className}`} aria-labelledby="notes-card-title">
      <div className="card-header flex-between">
        <h3 id="notes-card-title" className="card-title flex-center gap-sm">
          <StickyNote size={18} className="text-primary" />
          Private Notes ({notes.length})
        </h3>
        <span className="badge badge-subtle">Candidate Only</span>
      </div>

      <div className="card-body">
        {error && (
          <div className="alert alert-error mb-md" role="alert">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Add note form */}
        <form onSubmit={handleCreate} className="notes-form mb-lg">
          <label htmlFor="application-note-input" className="sr-only">
            Add a personal note
          </label>
          <div className="textarea-wrapper">
            <textarea
              id="application-note-input"
              rows={3}
              className="form-control"
              placeholder="Add recruiter details, application feedback, follow-up reminders..."
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              disabled={isSubmitting}
              maxLength={5000}
            />
          </div>
          <div className="flex-between mt-sm">
            <span className="text-xs text-muted">
              {newContent.length} / 5000 characters
            </span>
            <button
              type="submit"
              className="btn btn-primary btn-sm flex-center gap-xs"
              disabled={isSubmitting || !newContent.trim()}
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={14} className="spinner" />
                  Saving...
                </>
              ) : (
                <>
                  <Plus size={14} />
                  Add Note
                </>
              )}
            </button>
          </div>
        </form>

        {/* Notes list */}
        {notes.length === 0 ? (
          <div className="notes-empty text-center py-md">
            <p className="text-muted text-sm">
              No private notes yet. Add your thoughts, follow-up dates, or recruiter contacts above.
            </p>
          </div>
        ) : (
          <div className="notes-list">
            {notes.map((note) => (
              <div key={note.id} className="note-item">
                <div className="note-item-header flex-between">
                  <time className="note-date text-xs text-muted" dateTime={note.created_at}>
                    {formatDate(note.created_at)}
                  </time>
                  <button
                    type="button"
                    className="btn-icon text-muted hover-danger"
                    onClick={() => handleDelete(note.id)}
                    disabled={deletingId === note.id}
                    aria-label="Delete note"
                    title="Delete note"
                  >
                    {deletingId === note.id ? (
                      <Loader2 size={14} className="spinner" />
                    ) : (
                      <Trash2 size={14} />
                    )}
                  </button>
                </div>
                <p className="note-content">{note.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
