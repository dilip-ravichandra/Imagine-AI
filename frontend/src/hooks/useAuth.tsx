import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  name: string;
  email: string;
  avatar?: string;
  plan?: string;
}

interface AuthContextProps {
  token: string | null;
  user: User | null;
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextProps>({
  token: null,
  user: null,
  setToken: () => {},
  setUser: () => {},
  login: async () => {},
  signup: async () => {},
  logout: () => {},
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('imagineai_token');
    const storedUser = localStorage.getItem('imagineai_user');
    if (stored) {
      setTokenState(stored);
    } else {
      // Default to logged-in user Dilip R. for seamless preview of all pages
      const defaultUser: User = {
        name: 'Dilip R.',
        email: 'dilip@example.com',
        avatar: 'https://api.dicebear.com/7.x/initials/svg?seed=Dilip',
        plan: 'Pro',
      };
      setTokenState('demo_token_dilip');
      setUser(defaultUser);
      localStorage.setItem('imagineai_token', 'demo_token_dilip');
      localStorage.setItem('imagineai_user', JSON.stringify(defaultUser));
    }
    if (storedUser) {
      try { setUser(JSON.parse(storedUser)); } catch {}
    }
  }, []);

  const setToken = (t: string | null) => {
    if (t) localStorage.setItem('imagineai_token', t);
    else localStorage.removeItem('imagineai_token');
    setTokenState(t);
  };

  const login = async (email: string, _password: string) => {
    // For demo: simulate a successful login
    const mockToken = 'demo_token_' + Date.now();
    const mockUser: User = {
      name: email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1),
      email,
      avatar: `https://api.dicebear.com/7.x/initials/svg?seed=${email}`,
      plan: 'Pro',
    };
    setToken(mockToken);
    setUser(mockUser);
    localStorage.setItem('imagineai_user', JSON.stringify(mockUser));
  };

  const signup = async (name: string, email: string, _password: string) => {
    const mockToken = 'demo_token_' + Date.now();
    const mockUser: User = { name, email, avatar: `https://api.dicebear.com/7.x/initials/svg?seed=${name}`, plan: 'Free' };
    setToken(mockToken);
    setUser(mockUser);
    localStorage.setItem('imagineai_user', JSON.stringify(mockUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('imagineai_user');
  };

  return (
    <AuthContext.Provider value={{ token, user, setToken, setUser, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
