import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { DEMO_USERS } from '../../data/mockData';
import {
  Lock,
  User,
  Mail,
  ShieldCheck,
  Building2,
  Sparkles,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  X,
  KeyRound,
  Layers,
} from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose?: () => void;
  forceOpen?: boolean;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, forceOpen = false }) => {
  const { login, register, isLoading, error, clearError, user } = useAuth();
  const { config } = useApp();

  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!isOpen && !forceOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setValidationError(null);
    setSuccessMsg(null);

    if (tab === 'login') {
      if (!username.trim() || !password.trim()) {
        setValidationError('Por favor ingrese usuario y contraseña');
        return;
      }
      try {
        await login(username.trim(), password);
        if (onClose) onClose();
      } catch (err: any) {
        // error set in context
      }
    } else {
      // Register validation according to FastAPI constraints
      if (username.length < 4 || username.length > 128) {
        setValidationError('El nombre de usuario debe tener entre 4 y 128 caracteres.');
        return;
      }
      if (!email.includes('@') || email.length < 8) {
        setValidationError('Ingrese un correo electrónico institucional válido (8-256 caracteres).');
        return;
      }
      if (password.length < 8 || password.length > 128) {
        setValidationError('La contraseña debe tener al menos 8 caracteres.');
        return;
      }
      if (password !== confirmPassword) {
        setValidationError('Las contraseñas no coinciden.');
        return;
      }

      try {
        await register({
          username: username.trim(),
          email: email.trim(),
          password,
        });
        setSuccessMsg('¡Usuario registrado con éxito! Ya puedes iniciar sesión.');
        setTab('login');
      } catch (err: any) {
        // error set in context
      }
    }
  };

  const handleDemoSelect = async (demoUser: typeof DEMO_USERS[0]) => {
    clearError();
    setValidationError(null);
    try {
      await login(demoUser.username, '12345678');
      if (onClose) onClose();
    } catch {
      // handled in context
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Banner / Header */}
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 relative">
          {onClose && !forceOpen && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-white rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}

          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-indigo-500/20 border border-indigo-400/30 rounded-xl text-indigo-300">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-semibold tracking-wider text-indigo-300 uppercase">
                Veeduría Distrital • Distrito Capital
              </span>
              <h2 className="text-xl font-bold text-white">Índice de Innovación Pública</h2>
            </div>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed mt-1">
            Plataforma de recolección de evidencias y diagnóstico para entidades distritales y administradores.
          </p>

          <div className="mt-3 flex items-center gap-2 text-[11px] text-slate-400">
            <span className="inline-flex items-center gap-1 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700 font-mono text-[10px] text-slate-300">
              <KeyRound className="w-3 h-3 text-emerald-400" /> Auth JWT Ed25519
            </span>
            <span className="inline-flex items-center gap-1 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700 font-mono text-[10px] text-slate-300">
              X-Platform: {config.platform}
            </span>
            <span className="inline-flex items-center gap-1 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700 text-[10px] text-indigo-300">
              {config.useRealBackend ? '● FastAPI' : '● Mock Local'}
            </span>
          </div>
        </div>

        {/* Demo Quick Access */}
        <div className="p-5 bg-slate-50 border-b border-slate-200">
          <div className="flex items-center justify-between mb-2.5">
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" /> Acceso Rápido con Perfiles de Demostración
            </span>
            <span className="text-[11px] text-slate-500">1-Clic</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {DEMO_USERS.map((demo) => {
              const isAdmin = demo.role === 'admin';
              return (
                <button
                  key={demo.id}
                  onClick={() => handleDemoSelect(demo)}
                  disabled={isLoading}
                  className={`p-2.5 rounded-xl border text-left transition-all flex items-start gap-2.5 hover:shadow-xs group ${
                    isAdmin
                      ? 'bg-amber-50/70 border-amber-200 hover:border-amber-400 text-amber-950'
                      : 'bg-white border-slate-200 hover:border-indigo-400 text-slate-800'
                  }`}
                >
                  <div
                    className={`p-1.5 rounded-lg mt-0.5 ${
                      isAdmin ? 'bg-amber-100 text-amber-800' : 'bg-indigo-50 text-indigo-700'
                    }`}
                  >
                    {isAdmin ? <ShieldCheck className="w-4 h-4" /> : <Building2 className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs truncate">{demo.username}</span>
                      <span
                        className={`text-[10px] px-1.5 py-0.2 rounded font-medium ${
                          isAdmin ? 'bg-amber-200/60 text-amber-900' : 'bg-indigo-100 text-indigo-800'
                        }`}
                      >
                        {isAdmin ? 'Admin' : 'Entidad'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate mt-0.5">{demo.actor_label || demo.email}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-200">
          <button
            type="button"
            onClick={() => {
              setTab('login');
              clearError();
              setValidationError(null);
            }}
            className={`flex-1 py-3 text-xs font-semibold text-center border-b-2 transition-colors ${
              tab === 'login'
                ? 'border-indigo-600 text-indigo-700 bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-700 bg-slate-50'
            }`}
          >
            Iniciar Sesión con Credenciales
          </button>
          <button
            type="button"
            onClick={() => {
              setTab('register');
              clearError();
              setValidationError(null);
            }}
            className={`flex-1 py-3 text-xs font-semibold text-center border-b-2 transition-colors ${
              tab === 'register'
                ? 'border-indigo-600 text-indigo-700 bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-700 bg-slate-50'
            }`}
          >
            Registrar Nueva Cuenta
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {(error || validationError) && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-rose-600" />
              <div>
                <span className="font-semibold block">Error de autenticación</span>
                <span>{validationError || error}</span>
              </div>
            </div>
          )}

          {successMsg && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0 text-emerald-600" />
              <span>{successMsg}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Nombre de Usuario</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="ej: sdp.innovacion o admin.veeduria"
                className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              />
            </div>
          </div>

          {tab === 'register' && (
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Correo Institucional</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ej: innovacion@entidad.gov.co"
                  className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Contraseña</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono"
              />
            </div>
          </div>

          {tab === 'register' && (
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Confirmar Contraseña</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono"
                />
              </div>
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-xl shadow-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>{tab === 'login' ? 'Ingresar a la Plataforma' : 'Crear Cuenta y Activar'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Footer info */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 text-center">
          <p className="text-[11px] text-slate-500">
            {tab === 'login'
              ? '¿No tienes cuenta? Cambia a la pestaña "Registrar Nueva Cuenta" para activación inmediata sin confirmación por correo.'
              : 'El registro no requiere confirmación por correo y activa tu cuenta de inmediato.'}
          </p>
        </div>
      </div>
    </div>
  );
};
