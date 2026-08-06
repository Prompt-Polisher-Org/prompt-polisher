'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, 
  Settings, 
  BarChart2, 
  Menu, 
  X, 
  LogOut, 
  Wand2, 
  ChevronDown
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import styles from './Dashboard.module.scss';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, logout, fetchCurrentUser } = useAuthStore();
  
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    // Initial auth check if not already authenticated
    if (!isAuthenticated && !isLoading) {
      fetchCurrentUser();
    }
  }, [isAuthenticated, isLoading, fetchCurrentUser]);

  // Auth guard
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  const navItems = [
    { label: 'Chat', icon: <MessageSquare size={20} />, href: '/dashboard' },
    { label: 'Prompt Library', icon: <Wand2 size={20} />, href: '/dashboard/library' },
    { label: 'Analytics', icon: <BarChart2 size={20} />, href: '/dashboard/analytics' },
    { label: 'Settings', icon: <Settings size={20} />, href: '/dashboard/settings' },
  ];

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  const getInitials = (name: string | null) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  return (
    <div className={styles.dashboardContainer}>
      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div className={styles.overlay} onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`${styles.sidebar} ${!sidebarOpen ? styles.collapsed : ''} ${mobileMenuOpen ? styles.mobileOpen : ''}`}>
        <div className={styles.logoContainer}>
          <div className={styles.logoIcon}>
            <Wand2 size={20} color="white" />
          </div>
          <span className={styles.logoText}>Prompt Polisher</span>
        </div>

        <nav className={styles.nav}>
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link 
                key={item.href} 
                href={item.href}
                className={`${styles.navItem} ${isActive ? styles.active : ''}`}
                title={!sidebarOpen ? item.label : undefined}
                onClick={() => setMobileMenuOpen(false)}
              >
                {item.icon}
                <span className={styles.navLabel}>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className={styles.mainContent}>
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <button 
              className={styles.menuBtn} 
              onClick={() => {
                if (window.innerWidth <= 768) {
                  setMobileMenuOpen(!mobileMenuOpen);
                } else {
                  setSidebarOpen(!sidebarOpen);
                }
              }}
            >
              <Menu size={20} />
            </button>
            <h2 className="text-lg font-semibold md:hidden">Prompt Polisher</h2>
          </div>

          <div className={styles.headerRight}>
            <div className={styles.userDropdown}>
              <button 
                className={styles.userBtn}
                onClick={() => setDropdownOpen(!dropdownOpen)}
              >
                <div className={styles.avatar}>
                  {getInitials(user?.full_name)}
                </div>
                <span className="hidden md:inline-block text-sm text-slate-200 ml-2">
                  {user?.full_name || user?.email}
                </span>
                <ChevronDown size={16} className="text-slate-400" />
              </button>

              <AnimatePresence>
                {dropdownOpen && (
                  <motion.div 
                    className={styles.dropdownMenu}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    transition={{ duration: 0.15 }}
                  >
                    <div className="px-4 py-2 border-b border-slate-700/50 mb-1">
                      <p className="text-sm font-medium text-white">{user?.full_name}</p>
                      <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                    </div>
                    <button onClick={() => { setDropdownOpen(false); router.push('/dashboard/settings'); }}>
                      <Settings size={16} />
                      Preferences
                    </button>
                    <button className={styles.logoutBtn} onClick={() => logout()}>
                      <LogOut size={16} />
                      Sign out
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </header>

        <div className={styles.contentArea}>
          {children}
        </div>
      </main>
    </div>
  );
}
