import { createContext, useContext, useState, useCallback } from 'react';

// Change this if your API runs elsewhere.
export const API_BASE = 'http://localhost:8000';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem('smartwatch_token'));

  const login = useCallback(async (username, password) => {
    const form = new URLSearchParams();
    form.set('username', username);
    form.set('password', password);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    });

    if (!res.ok) {
      throw new Error(res.status === 401 ? 'Incorrect username or password' : `Login failed (${res.status})`);
    }

    const data = await res.json();
    sessionStorage.setItem('smartwatch_token', data.access_token);
    setToken(data.access_token);
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem('smartwatch_token');
    setToken(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, login, logout, isAuthenticated: Boolean(token) }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
