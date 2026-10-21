import React, { useState } from 'react';
import { AlertCircle, Lightbulb } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ROUTES } from '../../utils/router';

/**
 * Login único para entidades (/login/entidad).
 * Solo admite cuentas con rol de entidad: si entra un administrador, la sesión se cierra
 * y se muestra el aviso (los administradores usan /login).
 */
export const EntityLoginView: React.FC = () => {
  const { login, isLoading, error, clearError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setFormError(null);

    if (!email.trim() || !password) {
      setFormError('Por favor ingrese su correo y contraseña.');
      return;
    }

    try {
      await login(email.trim(), password, 'entity');
    } catch {
      // El mensaje queda en AuthContext (error).
    }
  };

  const message = error || formError;

  return (
    <div className="h-screen w-full relative flex items-center justify-center font-sans">
      <div className="absolute inset-0 z-0">
        <img src="/login-entidad-bg.jpg" alt="" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-white/40 backdrop-blur-sm" />
      </div>

      <div className="relative z-10 bg-white w-full max-w-md mx-4 p-10 rounded-3xl shadow-2xl border border-gray-100">
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-blue-200">
            <Lightbulb className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">LabCapital</h1>
          <p className="text-sm text-gray-500 mt-1">Plataforma de Innovación Pública</p>
        </div>

        {message && (
          <div className="mb-6 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-700 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{message}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Correo Electrónico
            </label>
            <input
              type="email"
              id="email"
              name="email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="usuario@entidad.gov.co"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <input
              type="password"
              id="password"
              name="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-3 px-4 rounded-xl text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200 shadow-lg shadow-blue-200 disabled:opacity-50 cursor-pointer"
          >
            {isLoading ? 'Validando credenciales...' : 'Iniciar Sesión'}
          </button>
        </form>

        <div className="mt-8 text-center text-sm text-gray-500">
          ¿No tienes una cuenta?{' '}
          <a href={ROUTES.login} className="font-semibold text-blue-600 hover:text-blue-500 transition-colors">
            Regístrate aquí
          </a>
        </div>
      </div>
    </div>
  );
};
