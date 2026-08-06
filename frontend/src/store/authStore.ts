import { create } from 'zustand';
import { api } from '@/lib/api';

interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  login: (tokens: { access_token: string; refresh_token: string }, user?: User) => void;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true, // Start true so we can check on mount

  login: (tokens, user) => {
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    
    if (user) {
      set({ user, isAuthenticated: true, isLoading: false });
    } else {
      // If user data wasn't provided, fetch it
      set({ isAuthenticated: true });
      get().fetchCurrentUser();
    }
  },

  logout: async () => {
    try {
      // Try to notify the backend (fire and forget)
      await api.post('/auth/logout');
    } catch (e) {
      console.error('Logout API failed, proceeding with local logout', e);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false, isLoading: false });
      
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  },

  fetchCurrentUser: async () => {
    set({ isLoading: true });
    try {
      // We rely on the API client interceptor to attach the token
      const response = await api.get('/users/me');
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch user', error);
      // Let the interceptor handle the 401/redirect
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  }
}));
