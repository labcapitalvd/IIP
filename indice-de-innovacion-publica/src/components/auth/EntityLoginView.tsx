import React, { useState } from 'react';
import { AlertCircle, Eye, EyeOff, Loader2 } from 'lucide-react';
import { IipLogo } from '../entity/wizard/IipLogo';
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
  const [showPassword, setShowPassword] = useState(false);

  const inputCls =
    'iip-focus w-full rounded-xl border border-iip-line bg-white px-4 py-3 text-[15px] text-iip-ink placeholder:text-slate-400';

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-iip-navy px-4 py-8 font-sans">
      <div className="pointer-events-none absolute -right-24 top-0 h-full w-40 -skew-x-[28deg] bg-iip-yellow/90" aria-hidden="true" />
      <div className="pointer-events-none absolute -left-32 bottom-0 h-72 w-72 rounded-full bg-iip-navy-700/60" aria-hidden="true" />

      <main className="relative z-10 w-full max-w-md">
        <div className="mb-6 flex justify-center">
          <IipLogo />
        </div>

        <div className="rounded-3xl bg-white p-8 shadow-2xl sm:p-10">
          <h1 className="text-2xl font-extrabold text-iip-ink">Ingreso de entidades</h1>
          <p className="mt-1 text-sm text-iip-muted">Acceda para diligenciar el formulario del Índice de Innovación Pública.</p>

          {message && (
            <div role="alert" className="mt-5 flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-sm text-rose-700">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{message}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-5" noValidate>
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-bold text-iip-ink">
                Correo electrónico
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
                aria-invalid={!!message || undefined}
                className={inputCls}
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-bold text-iip-ink">
                Contraseña
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  aria-invalid={!!message || undefined}
                  className={`${inputCls} pr-12`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                  aria-pressed={showPassword}
                  className="iip-focus absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-2 text-iip-muted hover:text-iip-ink"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="iip-focus flex w-full items-center justify-center gap-2 rounded-xl bg-iip-yellow px-4 py-3.5 text-[15px] font-extrabold text-iip-ink shadow-sm transition-colors hover:bg-iip-yellow-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading && <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />}
              {isLoading ? 'Validando credenciales…' : 'Iniciar sesión'}
            </button>
          </form>

          <p className="mt-7 text-center text-sm text-iip-muted">
            ¿No tienes una cuenta?{' '}
            <a href={ROUTES.login} className="iip-focus rounded font-bold text-iip-navy-700 underline-offset-2 hover:underline">
              Regístrate aquí
            </a>
          </p>
        </div>
      </main>
    </div>
  );
};
