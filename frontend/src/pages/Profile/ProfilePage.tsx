import React, { useEffect, useState, useCallback } from 'react'
import {
  User,
  Plus,
  Trash2,
  Edit2,
  Briefcase,
  GraduationCap,
  Sparkles,
  Check,
  X,
  MapPin,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import {
  addCandidateSkill,
  addEducation,
  addExperience,
  fetchCandidateProfile,
  removeCandidateSkill,
  removeEducation,
  removeExperience,
  updateCandidateProfile,
} from '../../services/profile'
import {
  CandidateProfile,
  CandidateProfileUpdate,
  ProficiencyLevel,
} from '../../types/profile'
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton'
import { ErrorMessage } from '../../components/common/ErrorMessage'

export const ProfilePage: React.FC = () => {
  const { token, user } = useAuth()

  const [profile, setProfile] = useState<CandidateProfile | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Edit basic info modal / inline form state
  const [isEditingInfo, setIsEditingInfo] = useState<boolean>(false)
  const [infoForm, setInfoForm] = useState<CandidateProfileUpdate>({})

  // Add skill form state
  const [isAddingSkill, setIsAddingSkill] = useState<boolean>(false)
  const [newSkillName, setNewSkillName] = useState<string>('')
  const [newSkillProficiency, setNewSkillProficiency] = useState<ProficiencyLevel>('INTERMEDIATE')
  const [newSkillYears, setNewSkillYears] = useState<string>('2')

  // Add experience form state
  const [isAddingExp, setIsAddingExp] = useState<boolean>(false)
  const [expCompany, setExpCompany] = useState<string>('')
  const [expTitle, setExpTitle] = useState<string>('')
  const [expStart, setExpStart] = useState<string>('')
  const [expEnd, setExpEnd] = useState<string>('')
  const [expCurrent, setExpCurrent] = useState<boolean>(false)
  const [expDesc, setExpDesc] = useState<string>('')

  // Add education form state
  const [isAddingEdu, setIsAddingEdu] = useState<boolean>(false)
  const [eduInstitution, setEduInstitution] = useState<string>('')
  const [eduDegree, setEduDegree] = useState<string>('')
  const [eduField, setEduField] = useState<string>('')

  const loadProfile = useCallback(async () => {
    if (!token) return
    setIsLoading(true)
    setError(null)

    try {
      const data = await fetchCandidateProfile(token)
      setProfile(data)
      setInfoForm({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        headline: data.headline || '',
        bio: data.bio || '',
        city: data.city || '',
        country: data.country || '',
        current_job_title: data.current_job_title || '',
        current_company: data.current_company || '',
        years_of_experience: data.years_of_experience ?? 0,
      })
    } catch (err: any) {
      setError(err.message || 'Failed to load candidate profile.')
    } finally {
      setIsLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  const flashSuccess = (msg: string) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 4000)
  }

  // Update basic profile info
  const handleSaveInfo = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token) return

    try {
      const updated = await updateCandidateProfile(token, infoForm)
      setProfile(updated)
      setIsEditingInfo(false)
      flashSuccess('Profile updated successfully.')
    } catch (err: any) {
      setError(err.message || 'Failed to update profile.')
    }
  }

  // Add candidate skill
  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !newSkillName.trim()) return

    try {
      await addCandidateSkill(token, {
        skill_name: newSkillName.trim(),
        proficiency: newSkillProficiency,
        years_experience: parseFloat(newSkillYears) || undefined,
      })
      setNewSkillName('')
      setIsAddingSkill(false)
      flashSuccess(`Added skill "${newSkillName.trim()}".`)
      loadProfile()
    } catch (err: any) {
      setError(err.message || 'Failed to add skill.')
    }
  }

  // Remove candidate skill
  const handleRemoveSkill = async (skillId: string, name: string) => {
    if (!token) return
    try {
      await removeCandidateSkill(token, skillId)
      flashSuccess(`Removed skill "${name}".`)
      loadProfile()
    } catch (err: any) {
      setError(err.message || 'Failed to remove skill.')
    }
  }

  // Add experience
  const handleAddExperience = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !expCompany.trim() || !expTitle.trim() || !expStart) return

    try {
      await addExperience(token, {
        company_name: expCompany.trim(),
        job_title: expTitle.trim(),
        start_date: expStart,
        end_date: expCurrent ? null : expEnd || null,
        is_current: expCurrent,
        description: expDesc.trim() || null,
      })
      setExpCompany('')
      setExpTitle('')
      setExpStart('')
      setExpEnd('')
      setExpDesc('')
      setIsAddingExp(false)
      flashSuccess('Added experience record.')
      loadProfile()
    } catch (err: any) {
      setError(err.message || 'Failed to add experience.')
    }
  }

  // Remove experience
  const handleRemoveExperience = async (expId: string) => {
    if (!token) return
    try {
      await removeExperience(token, expId)
      flashSuccess('Removed experience record.')
      loadProfile()
    } catch (err: any) {
      setError(err.message || 'Failed to remove experience.')
    }
  }

  // Add education
  const handleAddEducation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !eduInstitution.trim() || !eduDegree.trim()) return

    try {
      await addEducation(token, {
        institution_name: eduInstitution.trim(),
        degree: eduDegree.trim(),
        field_of_study: eduField.trim() || null,
      })
      setEduInstitution('')
      setEduDegree('')
      setEduField('')
      setIsAddingEdu(false)
      flashSuccess('Added education record.')
      loadProfile()
    } catch (err: any) {
      setError(err.message || 'Failed to add education.')
    }
  }

  // Remove education
  const handleRemoveEducation = async (eduId: string) => {
    if (!token) return
    try {
      await removeEducation(token, eduId)
      flashSuccess('Removed education record.')
      loadProfile()
    } catch (err: any) {
      setError(err.message || 'Failed to remove education.')
    }
  }

  if (isLoading) {
    return (
      <div className="profile-page-loading">
        <LoadingSkeleton count={3} type="card" />
      </div>
    )
  }

  return (
    <div className="profile-page">
      {/* Toast notifications */}
      {successMessage && (
        <div className="toast-success" role="status">
          <Check size={16} className="icon-mr" />
          {successMessage}
        </div>
      )}

      {error && <ErrorMessage message={error} onRetry={loadProfile} />}

      {/* Profile Overview Card */}
      <section className="card profile-hero-card">
        <div className="profile-hero-split">
          <div className="profile-hero-main">
            <div className="avatar-large">
              <User size={36} />
            </div>
            <div className="profile-hero-details">
              <h1 className="profile-name">
                {profile?.first_name || profile?.last_name
                  ? `${profile.first_name || ''} ${profile.last_name || ''}`.trim()
                  : user?.email}
              </h1>
              <p className="profile-headline text-accent">
                {profile?.headline || profile?.current_job_title || 'Software Engineer'}
              </p>
              <div className="profile-meta-chips">
                {(profile?.city || profile?.country) && (
                  <span className="meta-chip">
                    <MapPin size={13} className="icon-mr" />
                    {[profile.city, profile.country].filter(Boolean).join(', ')}
                  </span>
                )}
                {profile?.current_company && (
                  <span className="meta-chip">
                    <Briefcase size={13} className="icon-mr" />
                    {profile.current_company}
                  </span>
                )}
                {profile?.years_of_experience !== undefined && (
                  <span className="meta-chip">
                    {profile.years_of_experience} Years Exp
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="profile-hero-aside">
            <div className="completion-ring-box">
              <span className="completion-ring-val">{profile?.profile_completion_percent}%</span>
              <span className="completion-ring-label">Profile Match Readiness</span>
            </div>

            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setIsEditingInfo(!isEditingInfo)}
            >
              <Edit2 size={14} className="icon-mr" />
              {isEditingInfo ? 'Cancel' : 'Edit Profile'}
            </button>
          </div>
        </div>

        {/* Inline Edit Form */}
        {isEditingInfo && (
          <form onSubmit={handleSaveInfo} className="profile-edit-form mt-3">
            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">First Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={infoForm.first_name || ''}
                  onChange={(e) => setInfoForm({ ...infoForm, first_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Last Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={infoForm.last_name || ''}
                  onChange={(e) => setInfoForm({ ...infoForm, last_name: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Professional Headline</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Senior Full-Stack Engineer (React, Python, AWS)"
                value={infoForm.headline || ''}
                onChange={(e) => setInfoForm({ ...infoForm, headline: e.target.value })}
              />
            </div>

            <div className="form-grid-3">
              <div className="form-group">
                <label className="form-label">Current Job Title</label>
                <input
                  type="text"
                  className="form-input"
                  value={infoForm.current_job_title || ''}
                  onChange={(e) => setInfoForm({ ...infoForm, current_job_title: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Current Company</label>
                <input
                  type="text"
                  className="form-input"
                  value={infoForm.current_company || ''}
                  onChange={(e) => setInfoForm({ ...infoForm, current_company: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Years of Experience</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  className="form-input"
                  value={infoForm.years_of_experience ?? ''}
                  onChange={(e) =>
                    setInfoForm({
                      ...infoForm,
                      years_of_experience: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                />
              </div>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">City</label>
                <input
                  type="text"
                  className="form-input"
                  value={infoForm.city || ''}
                  onChange={(e) => setInfoForm({ ...infoForm, city: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Country</label>
                <input
                  type="text"
                  className="form-input"
                  value={infoForm.country || ''}
                  onChange={(e) => setInfoForm({ ...infoForm, country: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Summary / Bio</label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder="Brief summary of your technical background and career goals..."
                value={infoForm.bio || ''}
                onChange={(e) => setInfoForm({ ...infoForm, bio: e.target.value })}
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary btn-sm">
                Save Profile Changes
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setIsEditingInfo(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </section>

      {/* Skills Section */}
      <section className="card profile-section-card">
        <div className="card-header-clean">
          <div>
            <h3 className="section-title-sm">
              <Sparkles size={18} className="icon-mr text-accent" />
              Professional Skills & Proficiencies
            </h3>
            <p className="text-muted text-xs">
              Matching algorithms use your skills as primary criteria against job requirements.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-xs"
            onClick={() => setIsAddingSkill(!isAddingSkill)}
          >
            <Plus size={13} className="icon-mr" />
            Add Skill
          </button>
        </div>

        {/* Add skill input drawer */}
        {isAddingSkill && (
          <form onSubmit={handleAddSkill} className="add-subitem-form">
            <div className="form-inline-grid">
              <input
                type="text"
                className="form-input"
                placeholder="Skill name (e.g. React, Python, PostgreSQL)"
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                required
              />
              <select
                className="form-select"
                value={newSkillProficiency}
                onChange={(e) => setNewSkillProficiency(e.target.value as ProficiencyLevel)}
              >
                <option value="BEGINNER">Beginner</option>
                <option value="INTERMEDIATE">Intermediate</option>
                <option value="ADVANCED">Advanced</option>
                <option value="EXPERT">Expert</option>
              </select>
              <input
                type="number"
                step="0.5"
                min="0"
                className="form-input"
                placeholder="Years (optional)"
                value={newSkillYears}
                onChange={(e) => setNewSkillYears(e.target.value)}
              />
              <div className="btn-group">
                <button type="submit" className="btn btn-primary btn-sm">
                  Add
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setIsAddingSkill(false)}
                >
                  <X size={15} />
                </button>
              </div>
            </div>
          </form>
        )}

        {/* Skills Tag Cloud */}
        {profile?.skills && profile.skills.length > 0 ? (
          <div className="skills-cloud">
            {profile.skills.map((skill) => (
              <div key={skill.id} className="skill-chip">
                <span className="skill-chip-name">{skill.skill_name}</span>
                <span className="skill-chip-level">{skill.proficiency.toLowerCase()}</span>
                {skill.years_experience && (
                  <span className="skill-chip-years">{skill.years_experience}y</span>
                )}
                <button
                  type="button"
                  className="skill-chip-remove"
                  onClick={() => handleRemoveSkill(skill.id, skill.skill_name)}
                  aria-label={`Remove ${skill.skill_name}`}
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted text-sm" style={{ padding: '0.5rem 0' }}>
            No skills added yet. Add your core languages, frameworks, and tools to unlock match scores!
          </p>
        )}
      </section>

      {/* Experience Section */}
      <section className="card profile-section-card">
        <div className="card-header-clean">
          <div>
            <h3 className="section-title-sm">
              <Briefcase size={18} className="icon-mr text-accent" />
              Work Experience
            </h3>
            <p className="text-muted text-xs">
              Demonstrated experience is matched against minimum requirements.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-xs"
            onClick={() => setIsAddingExp(!isAddingExp)}
          >
            <Plus size={13} className="icon-mr" />
            Add Experience
          </button>
        </div>

        {/* Add experience form */}
        {isAddingExp && (
          <form onSubmit={handleAddExperience} className="add-subitem-form">
            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Job Title *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Senior Frontend Engineer"
                  value={expTitle}
                  onChange={(e) => setExpTitle(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Company Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Acme Corp"
                  value={expCompany}
                  onChange={(e) => setExpCompany(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Start Date *</label>
                <input
                  type="date"
                  className="form-input"
                  value={expStart}
                  onChange={(e) => setExpStart(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">End Date</label>
                <input
                  type="date"
                  className="form-input"
                  disabled={expCurrent}
                  value={expEnd}
                  onChange={(e) => setExpEnd(e.target.value)}
                />
                <label className="checkbox-label mt-1">
                  <input
                    type="checkbox"
                    checked={expCurrent}
                    onChange={(e) => setExpCurrent(e.target.checked)}
                  />
                  <span>Currently working here</span>
                </label>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Responsibilities & Achievements</label>
              <textarea
                className="form-textarea"
                rows={2}
                placeholder="Key tech stack used, systems built, impact..."
                value={expDesc}
                onChange={(e) => setExpDesc(e.target.value)}
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary btn-sm">
                Save Experience
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setIsAddingExp(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Experience List */}
        {profile?.experiences && profile.experiences.length > 0 ? (
          <div className="timeline-list">
            {profile.experiences.map((exp) => (
              <div key={exp.id} className="timeline-item">
                <div className="timeline-dot" />
                <div className="timeline-content">
                  <div className="timeline-header-line">
                    <span className="timeline-title">{exp.job_title}</span>
                    <button
                      type="button"
                      className="btn-icon btn-danger-icon"
                      onClick={() => handleRemoveExperience(exp.id)}
                      title="Remove experience"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                  <span className="timeline-company">{exp.company_name}</span>
                  <span className="timeline-dates">
                    {exp.start_date} – {exp.is_current ? 'Present' : exp.end_date || 'N/A'}
                  </span>
                  {exp.description && <p className="timeline-desc">{exp.description}</p>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted text-sm" style={{ padding: '0.5rem 0' }}>
            No work experience recorded yet.
          </p>
        )}
      </section>

      {/* Education Section */}
      <section className="card profile-section-card">
        <div className="card-header-clean">
          <div>
            <h3 className="section-title-sm">
              <GraduationCap size={18} className="icon-mr text-accent" />
              Education & Degrees
            </h3>
            <p className="text-muted text-xs">Degrees and academic credentials.</p>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-xs"
            onClick={() => setIsAddingEdu(!isAddingEdu)}
          >
            <Plus size={13} className="icon-mr" />
            Add Education
          </button>
        </div>

        {/* Add education form */}
        {isAddingEdu && (
          <form onSubmit={handleAddEducation} className="add-subitem-form">
            <div className="form-grid-3">
              <div className="form-group">
                <label className="form-label">Degree *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Bachelor of Science"
                  value={eduDegree}
                  onChange={(e) => setEduDegree(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Institution Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. University of California"
                  value={eduInstitution}
                  onChange={(e) => setEduInstitution(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Field of Study</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Computer Science"
                  value={eduField}
                  onChange={(e) => setEduField(e.target.value)}
                />
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary btn-sm">
                Save Education
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setIsAddingEdu(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Education List */}
        {profile?.educations && profile.educations.length > 0 ? (
          <div className="education-list">
            {profile.educations.map((edu) => (
              <div key={edu.id} className="education-card-item">
                <div>
                  <h4 className="edu-degree">{edu.degree}</h4>
                  <span className="edu-institution">{edu.institution_name}</span>
                  {edu.field_of_study && <span className="edu-field"> · {edu.field_of_study}</span>}
                </div>
                <button
                  type="button"
                  className="btn-icon btn-danger-icon"
                  onClick={() => handleRemoveEducation(edu.id)}
                  title="Remove education"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted text-sm" style={{ padding: '0.5rem 0' }}>
            No education entries added yet.
          </p>
        )}
      </section>
    </div>
  )
}
