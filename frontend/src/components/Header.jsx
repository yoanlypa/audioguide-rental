// src/components/Header.jsx
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.jsx';

export default function Header() {
  const { isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
        <Link to="/" className="text-2xl font-bold text-blue-700">
          Innovations Tours
        </Link>
        <nav className="flex space-x-4">
          <Link to="/" className="hover:text-blue-500 transition">Inicio</Link>
          {isAuthenticated && (
            <>
              <Link to="/mis-pedidos" className="hover:text-blue-500 transition">
                Mis pedidos
              </Link>
              <button
                onClick={logout}
                className="text-red-500 hover:text-red-700 transition"
              >
                Cerrar sesión
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
