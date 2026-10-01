import React, { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Briefcase,
  Bookmark,
  Bell,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  Radar,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { fetchNotifications } from '../../services/notifications'

export const AppLayout: React.FC = () => {
  const { user, token, logout } = useAuth()
  const navigate = useNavigate()
  const [unreadCount, setUnreadCount] = useState<number>(0)
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false)

  // Fetch unread count periodically or on route change
  useEffect(() => {
    let isMounted = true
    if (!token) return

    const loadUnread = async () => {
      try {
        const res = await fetchNotifications(token, { unreadOnly: true, limit: 1 })
        if (isMounted) {
          setUnreadCount(res.unread_count || 0)
        }
      } catch {
        // Silently fail badge check if offline
      }
    }

    loadUnread()
    const interval = setInterval(loadUnread, 60000) // gentle 60s poll

    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [token])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const closeMobileMenu = () => {
    setMobileMenuOpen(false)
  }

  return (
    <div className="app-shell">
      {/* Top Navbar */}
      <header className="app-header">
        <div className="header-inner">
          <div className="header-left">
            <Link to="/dashboard" className="brand-logo" onClick={closeMobileMenu}>
              <div className="brand-icon-box">
                <Radar size={22} className="brand-icon" />
              </div>
              <span className="brand-name">JobWatch AI</span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="nav-desktop" aria-label="Main Navigation">
              <NavLink
                to="/dashboard"
                className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
              >
                <LayoutDashboard size={16} className="nav-icon" />
                <span>Dashboard</span>
              </NavLink>

              <NavLink
                to="/jobs"
                className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
              >
                <Briefcase size={16} className="nav-icon" />
                <span>Jobs</span>
              </NavLink>

              <NavLink
                to="/saved"
                className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
              >
                <Bookmark size={16} className="nav-icon" />
                <span>Saved</span>
              </NavLink>

              <NavLink
                to="/notifications"
                className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
              >
                <div className="nav-icon-badge-wrap">
                  <Bell size={16} className="nav-icon" />
                  {unreadCount > 0 && (
                    <span className="notification-badge" aria-label={`${unreadCount} unread alerts`}>
                      {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                  )}
                </div>
                <span>Alerts</span>
              </NavLink>
            </nav>
          </div>

          <div className="header-right">
            {/* User profile & settings navigation */}
            <div className="user-desktop-nav">
              <NavLink
                to="/profile"
                className={({ isActive }) => `user-profile-pill ${isActive ? 'active' : ''}`}
                title="Candidate Profile"
              >
                <div className="avatar-circle">
                  <User size={15} />
                </div>
                <span className="user-email-text">{user?.email || 'Candidate'}</span>
              </NavLink>

              <NavLink
                to="/settings"
                className={({ isActive }) => `btn-icon ${isActive ? 'active' : ''}`}
                title="Preferences & Settings"
                aria-label="Settings"
              >
                <Settings size={18} />
              </NavLink>

              <button
                type="button"
                className="btn-icon btn-logout"
                onClick={handleLogout}
                title="Sign out"
                aria-label="Sign out"
              >
                <LogOut size={18} />
              </button>
            </div>

            {/* Mobile hamburger toggle */}
            <button
              type="button"
              className="btn-icon mobile-menu-btn"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="mobile-nav-drawer" role="dialog" aria-modal="true">
            <div className="mobile-user-info">
              <div className="avatar-circle">
                <User size={16} />
              </div>
              <span className="mobile-email">{user?.email}</span>
            </div>

            <nav className="mobile-nav-links">
              <NavLink
                to="/dashboard"
                className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}
                onClick={closeMobileMenu}
              >
                <LayoutDashboard size={18} />
                <span>Dashboard</span>
              </NavLink>

              <NavLink
                to="/jobs"
                className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}
                onClick={closeMobileMenu}
              >
                <Briefcase size={18} />
                <span>Discover Jobs</span>
              </NavLink>

              <NavLink
                to="/saved"
                className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}
                onClick={closeMobileMenu}
              >
                <Bookmark size={18} />
                <span>Saved Jobs</span>
              </NavLink>

              <NavLink
                to="/notifications"
                className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}
                onClick={closeMobileMenu}
              >
                <Bell size={18} />
                <span>Alerts & Notifications</span>
                {unreadCount > 0 && (
                  <span className="badge badge-accent ml-auto">{unreadCount}</span>
                )}
              </NavLink>

              <NavLink
                to="/profile"
                className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}
                onClick={closeMobileMenu}
              >
                <User size={18} />
                <span>Candidate Profile</span>
              </NavLink>

              <NavLink
                to="/settings"
                className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}
                onClick={closeMobileMenu}
              >
                <Settings size={18} />
                <span>Settings & Alerts</span>
              </NavLink>

              <button
                type="button"
                className="mobile-nav-link mobile-logout-link"
                onClick={() => {
                  closeMobileMenu()
                  handleLogout()
                }}
              >
                <LogOut size={18} />
                <span>Sign Out</span>
              </button>
            </nav>
          </div>
        )}
      </header>

      {/* Main Page Content */}
      <main className="app-main-content">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-inner">
          <p className="footer-copy">
            JobWatch AI · Autonomous Career Opportunity Intelligence
          </p>
          <div className="footer-links">
            <span className="footer-badge">Phase 9 UI</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
