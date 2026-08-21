import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import {
  Lock,
  User,
  Mail,
  Building2,
  Phone,
  UserCheck,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

export const LoginView: React.FC = () => {
  const { login, register, isLoading, error, clearError } = useAuth();
  const { actors, config } = useApp();

  const [mode, setMode] = useState<'login' | 'register'>('login');

  // Login Form State
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register Form State
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regActorId, setRegActorId] = useState(actors[0]?.id || 'act-001');
  const [regContactPerson, setRegContactPerson] = useState('');
  const [regPhone, setRegPhone] = useState('');

  const [registrationSuccess, setRegistrationSuccess] = useState<{
    username: string;
    actorLabel: string;
  } | null>(null);

  const [formError, setFormError] = useState<string | null>(null);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setFormError(null);

    if (!loginUsername.trim() || !loginPassword.trim()) {
      setFormError('Por favor ingrese su usuario y contraseña.');
      return;
    }

    try {
      await login(loginUsername.trim(), loginPassword);
    } catch {
      // Error message is set in AuthContext
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setFormError(null);
    setRegistrationSuccess(null);

    if (!regUsername.trim() || !regEmail.trim() || !regPassword.trim()) {
      setFormError('Por favor complete todos los campos obligatorios.');
      return;
    }

    // Mirrors the backend's Pydantic constraints (UsernameSchema /
    // UserPasswordSchema) so real registration doesn't fail with a 422
    // that this form could have caught locally.
    if (regUsername.trim().length < 4 || regUsername.trim().length > 128) {
      setFormError('El usuario debe tener entre 4 y 128 caracteres.');
      return;
    }

    if (regEmail.trim().length < 8 || regEmail.trim().length > 256) {
      setFormError('Ingrese un correo electrónico institucional válido.');
      return;
    }

    if (regPassword.length < 8 || regPassword.length > 128) {
      setFormError('La contraseña debe tener entre 8 y 128 caracteres.');
      return;
    }

    const selectedActor = actors.find((a) => a.id === regActorId);

    try {
      await register({
        username: regUsername.trim(),
        email: regEmail.trim(),
        password: regPassword,
        actor_id: regActorId,
        actor_label: selectedActor?.label || 'Entidad Distrital',
        contact_person: regContactPerson.trim() || undefined,
        phone: regPhone.trim() || undefined,
      });

      setRegistrationSuccess({
        username: regUsername.trim(),
        actorLabel: selectedActor?.label || 'la entidad seleccionada',
      });

      // Clear register fields
      setRegUsername('');
      setRegEmail('');
      setRegPassword('');
      setRegContactPerson('');
      setRegPhone('');
    } catch (err: any) {
      // Handled via context or error message
    }
  };

  const handleQuickDemoLogin = async (username: string, roleType: 'admin' | 'entity') => {
    clearError();
    setFormError(null);
    try {
      if (roleType === 'admin') {
        await login(username, 'admin1234');
      } else {
        await login(username, '12345678');
      }
    } catch {
      // error handled
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-between text-slate-100 font-sans relative overflow-hidden">
      {/* Background Subtle Accent Gradients */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Institutional Ribbon */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-xs px-4 sm:px-8 py-3 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2 font-bold text-slate-300">
          <span className="w-2 h-2 rounded-full bg-amber-400" />
          <span>Alcaldía Mayor de Bogotá D.C.</span>
          <span className="text-slate-700">•</span>
          <span className="text-amber-400 font-bold">Veeduría Distrital / LabCapital</span>
        </div>
        <div className="text-[11px] text-slate-400 hidden sm:block">
          Índice de Innovación Pública (IIP)
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6 my-auto z-10">
        <div className="w-full max-w-md bg-slate-950 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6">
          {/* Official Logo Banner */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center justify-center bg-white rounded-2xl p-3 shadow-md border border-slate-200/40">
              <img
                src="https://labcapital.veeduriadistrital.gov.co:4282/wp-content/uploads/2026/06/Captura-de-pantalla-2026-06-10-133932.png"
                alt="LabCapital - Veeduría Distrital"
                className="h-12 w-auto max-w-[240px] object-contain"
                referrerPolicy="no-referrer"
                onError={(e) => {
                  const target = e.currentTarget;
                  target.style.display = 'none';
                  if (target.parentElement) {
                    target.parentElement.innerHTML = `<span class="text-sm font-black text-slate-900 px-2 py-1">LabCapital • Veeduría Distrital</span>`;
                  }
                }}
              />
            </div>

            <div>
              <h1 className="text-xl font-black text-white tracking-tight">
                Índice de Innovación Pública
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Plataforma Distrital de Medición, Diagnóstico y Formularios IIP
              </p>
            </div>
          </div>

          {/* Mode Switcher Tabs (Iniciar Sesión vs Registrarse) */}
          <div className="flex bg-slate-900 p-1 rounded-2xl border border-slate-800 text-xs">
            <button
              type="button"
              onClick={() => {
                setMode('login');
                clearError();
                setFormError(null);
              }}
              className={`flex-1 py-2 rounded-xl font-bold transition-all text-center ${
                mode === 'login'
                  ? 'bg-amber-500 text-slate-950 shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Iniciar Sesión
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('register');
                clearError();
                setFormError(null);
                setRegistrationSuccess(null);
              }}
              className={`flex-1 py-2 rounded-xl font-bold transition-all text-center ${
                mode === 'register'
                  ? 'bg-amber-500 text-slate-950 shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Registrarse
            </button>
          </div>

          {/* Success Banner after registration */}
          {registrationSuccess && mode === 'login' && (
            <div className="p-4 bg-emerald-950/60 border border-emerald-500/40 rounded-2xl text-xs space-y-2 animate-in fade-in">
              <div className="flex items-start gap-2.5 text-emerald-400 font-bold">
                <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                <span>¡Registro recibido exitosamente!</span>
              </div>
              <p className="text-emerald-200/90 leading-relaxed text-[11px]">
                El usuario <strong className="text-white font-mono">{registrationSuccess.username}</strong> ha sido registrado para <strong>{registrationSuccess.actorLabel}</strong>.
              </p>
              {config.useRealBackend ? (
                <div className="flex items-center gap-1.5 p-2 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-emerald-300 text-[11px]">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                  <span>
                    <strong>Cuenta activa.</strong> Ya puede iniciar sesión con su usuario y contraseña.
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 p-2 bg-amber-950/40 border border-amber-500/30 rounded-xl text-amber-300 text-[11px]">
                  <Clock className="w-3.5 h-3.5 shrink-0" />
                  <span>
                    <strong>Estado: Pendiente.</strong> Podrá ingresar una vez la entidad o el administrador le otorgue el permiso de acceso.
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Error Message Display */}
          {(error || formError) && (
            <div className="p-3.5 bg-rose-950/50 border border-rose-500/40 rounded-2xl text-xs text-rose-200 flex items-start gap-2.5 animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-bold text-rose-300">Aviso del Sistema</div>
                <div className="leading-relaxed text-[11px]">{error || formError}</div>
              </div>
            </div>
          )}

          {/* LOGIN FORM (Simple: Usuario y Contraseña) */}
          {mode === 'login' ? (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-300">Usuario</label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={loginUsername}
                    onChange={(e) => setLoginUsername(e.target.value)}
                    placeholder="Ej. admin.veeduria o sdp.innovacion"
                    className="w-full pl-9 pr-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-amber-400 focus:ring-1 focus:ring-amber-400"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-300">Contraseña</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-amber-400 focus:ring-1 focus:ring-amber-400"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold rounded-xl text-xs shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isLoading ? (
                  <span>Validando credenciales...</span>
                ) : (
                  <>
                    <span>Ingresar al Sistema</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              {/* Quick Demo Access — mock-mode only. Against the real backend
                  these demo credentials don't correspond to real seeded
                  users, so surfacing them here would just produce confusing
                  InvalidCredentials errors. */}
              {!config.useRealBackend && (
              <div className="pt-3 border-t border-slate-800/80 space-y-2">
                <div className="text-[11px] font-semibold text-slate-400 text-center">
                  Acceso Rápido de Prueba (Demostración)
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => handleQuickDemoLogin('admin.veeduria', 'admin')}
                    className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-xl text-[11px] text-left transition-colors flex items-center gap-2"
                  >
                    <ShieldCheck className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <div>
                      <div className="font-bold text-slate-200">Admin General</div>
                      <div className="text-[9px] text-slate-400">Veeduría Distrital</div>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleQuickDemoLogin('sdp.innovacion', 'entity')}
                    className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-xl text-[11px] text-left transition-colors flex items-center gap-2"
                  >
                    <Building2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                    <div>
                      <div className="font-bold text-slate-200">Entidad Distrital</div>
                      <div className="text-[9px] text-slate-400">Planeación (SDP)</div>
                    </div>
                  </button>
                </div>
              </div>
              )}
            </form>
          ) : (
            /* REGISTRATION FORM (Auto-registro de usuarios de entidades con aprobación requerida) */
            <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
              {config.useRealBackend ? (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-[11px] text-emerald-300 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-400" />
                  <div className="leading-relaxed">
                    <strong>Registro directo:</strong> Su cuenta queda activa de inmediato, sin verificación por correo ni aprobación adicional.
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-2xl text-[11px] text-amber-300 flex items-start gap-2">
                  <Clock className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
                  <div className="leading-relaxed">
                    <strong>Política de Autorización:</strong> Al registrarse, su usuario quedará en estado <strong>Pendiente</strong>. No podrá ingresar hasta que la entidad seleccionada valide y apruebe su cuenta.
                  </div>
                </div>
              )}

              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-300">
                  Entidad Distrital a la que pertenece <span className="text-amber-400">*</span>
                </label>
                <div className="relative">
                  <Building2 className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <select
                    value={regActorId}
                    onChange={(e) => setRegActorId(e.target.value)}
                    required
                    className="w-full pl-9 pr-3.5 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-hidden focus:border-amber-400"
                  >
                    {actors.map((act) => (
                      <option key={act.id} value={act.id}>
                        {act.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-300">
                    Usuario <span className="text-amber-400">*</span>
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      required
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      placeholder="ej. juan.perez"
                      className="w-full pl-8 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-amber-400"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-300">
                    Contraseña <span className="text-amber-400">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="password"
                      required
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="Mínimo 8 carácteres"
                      className="w-full pl-8 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-amber-400"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-300">
                  Correo Electrónico Institucional <span className="text-amber-400">*</span>
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="usuario@entidad.gov.co"
                    className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-amber-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-300">
                    Nombre del Funcionario
                  </label>
                  <input
                    type="text"
                    value={regContactPerson}
                    onChange={(e) => setRegContactPerson(e.target.value)}
                    placeholder="Ej. Juan Pérez"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-amber-400"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-300">Teléfono / Ext.</label>
                  <div className="relative">
                    <Phone className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={regPhone}
                      onChange={(e) => setRegPhone(e.target.value)}
                      placeholder="Ej. 3358000 Ext 240"
                      className="w-full pl-8 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-amber-400"
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold rounded-xl text-xs shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 mt-2"
              >
                {isLoading ? (
                  <span>Enviando registro...</span>
                ) : (
                  <>
                    <UserCheck className="w-4 h-4" />
                    <span>{config.useRealBackend ? 'Registrar Cuenta' : 'Registrar Cuenta (Pendiente de Aprobación)'}</span>
                  </>
                )}
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => setMode('login')}
                  className="text-xs text-amber-400 hover:text-amber-300 font-semibold"
                >
                  ¿Ya tiene una cuenta aprobada? Iniciar sesión
                </button>
              </div>
            </form>
          )}
        </div>
      </main>

      {/* Institutional Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/80 px-4 py-3 text-center text-xs text-slate-400">
        <div>Alcaldía Mayor de Bogotá D.C. • Veeduría Distrital • Laboratorio de Innovación Pública (LabCapital)</div>
      </footer>
    </div>
  );
};
