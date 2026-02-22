import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

export interface User {
  name: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (name: string, email: string, password: string, role: User['role']) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const STORAGE_KEY = 'prakalp_auth';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  // Restore session on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setUser(JSON.parse(stored));
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    // Check registered users
    const usersRaw = localStorage.getItem('prakalp_users');
    const users: Array<{ name: string; email: string; password: string; role: User['role'] }> =
      usersRaw ? JSON.parse(usersRaw) : [];

    const found = users.find(u => u.email === email && u.password === password);
    if (found) {
      const u: User = { name: found.name, email: found.email, role: found.role };
      setUser(u);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
      return true;
    }

    // Fallback demo credentials
    if (email === 'admin@prakalp.in' && password === 'admin123') {
      const u: User = { name: 'Admin', email, role: 'admin' };
      setUser(u);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
      return true;
    }

    return false;
  };

  const signup = async (
    name: string,
    email: string,
    password: string,
    role: User['role'],
  ): Promise<boolean> => {
    const usersRaw = localStorage.getItem('prakalp_users');
    const users: Array<{ name: string; email: string; password: string; role: User['role'] }> =
      usersRaw ? JSON.parse(usersRaw) : [];

    if (users.some(u => u.email === email)) {
      return false; // already exists
    }

    users.push({ name, email, password, role });
    localStorage.setItem('prakalp_users', JSON.stringify(users));

    // Auto-login after signup
    const u: User = { name, email, role };
    setUser(u);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
    return true;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
