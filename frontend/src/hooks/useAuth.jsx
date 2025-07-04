import { createContext, useContext, useState } from 'react';
import api from '../services/api.js';

// Simple JWT decoder without external library
function jwtDecode(token) {
  try {
    const payload = token.split('.')[1];
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const access = localStorage.getItem('access');
    return access ? jwtDecode(access) : null;
  });

const login = async (email, password) => {
  try {
    const { data } = await api.post('api/token/', {email,password});
    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
    setUser(jwtDecode(data.access));
  } catch (error) {
    if (error.response && error.response.data) {
      console.error('Login error:', error.response.data);
      throw new Error(error.response.data.detail || 'Credenciales incorrectas');
    } else {
      console.error('Unexpected login error:', error);
      throw new Error('Error inesperado al iniciar sesión');
    }
  }
};

  const logout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    setUser(null);
  };

  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
