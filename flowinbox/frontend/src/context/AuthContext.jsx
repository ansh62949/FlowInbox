import React, { createContext, useContext, useState, useEffect } from 'react';
import authApi from '../api/auth';

const AuthContext = createContext({
  user: null,
  authenticated: false,
  loading: true,
  llmLabel: 'Groq (Llama 3 70B)',
  refreshAuth: () => {},
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [llmLabel, setLlmLabel] = useState('Groq (Llama 3 70B)');
  const [theme, setThemeState] = useState(() => localStorage.getItem('flowinbox_theme') || 'cream');

  const setTheme = (newTheme) => {
    setThemeState(newTheme);
    localStorage.setItem('flowinbox_theme', newTheme);
  };

  useEffect(() => {
    document.documentElement.classList.remove('theme-cream', 'theme-dark', 'theme-slate');
    document.documentElement.classList.add(`theme-${theme}`);
  }, [theme]);

  const fetchCurrentUser = async () => {
    try {
      setLoading(true);
      const data = await authApi.getMe();
      if (data && data.authenticated && data.user) {
        setUser(data.user);
        setAuthenticated(true);
        if (data.access_token) {
          localStorage.setItem('flowinbox_token', data.access_token);
        }
        if (data.llm_label) {
          setLlmLabel(data.llm_label);
        }
      } else {
        setUser(null);
        setAuthenticated(false);
      }
    } catch (err) {
      console.error('[AuthContext] Failed to load current user:', err);
      setUser(null);
      setAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const completeOnboarding = async () => {
    try {
      await authApi.completeOnboarding();
      setUser((prevUser) => (prevUser ? { ...prevUser, has_completed_onboarding: true } : prevUser));
      localStorage.setItem('flowinbox_onboarding_completed', 'true');
      await fetchCurrentUser();
    } catch (err) {
      console.error('[AuthContext] Error completing onboarding:', err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        authenticated,
        loading,
        llmLabel,
        theme,
        setTheme,
        refreshAuth: fetchCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export default AuthContext;
