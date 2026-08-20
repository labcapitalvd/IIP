import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import {
  ShieldCheck,
  Building2,
  Settings,
  LogOut,
  ChevronDown,
} from 'lucide-react';

interface HeaderProps {
  onOpenSettings: () => void;
  onOpenLogs?: () => void;
  onOpenAuthModal?: () => void;
  onOpenDockerModal?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenSettings,
}) => {
  const { user, role, switchRole, switchEntity, logout } = useAuth();
  const { actors } = useApp();
  const [showEntityDropdown, setShowEntityDropdown] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const activeActor = actors.find((a) => a.id === user?.actor_id) || actors[0];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-30 shadow-md select-none">
      {/* Institutional Top Ribbon (Bogotá D.C. & Veeduría Distrital) */}
      <div className="bg-slate-950 px-4 sm:px-6 lg:px-8 py-1.5 border-b border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-bold text-slate-300">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span className="tracking-wider uppercase text-[10px]">Alcaldía Mayor de Bogotá D.C.</span>
          </div>
          <span className="text-slate-700 hidden sm:inline">|</span>
          <span className="text-slate-400 font-medium">
            Veeduría Distrital • <strong className="text-amber-400 font-bold">LabCapital</strong>
          </span>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-slate-400">
          <span className="hidden sm:inline font-medium">Sistema Distrital de Medición</span>
        </div>
      </div>

      {/* Main App Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-18 gap-4">
          {/* Official Logo & Brand */}
          <div className="flex items-center gap-3 sm:gap-4 min-w-0">
            <div className="flex items-center bg-white/95 rounded-xl px-2.5 py-1.5 shadow-xs border border-white/20 shrink-0">
              <img
                src="https://labcapital.veeduriadistrital.gov.co:4282/wp-content/uploads/2026/06/Captura-de-pantalla-2026-06-10-133932.png"
                alt="LabCapital - Veeduría Distrital"
                className="h-8 sm:h-10 w-auto max-w-[180px] sm:max-w-[220px] object-contain"
                referrerPolicy="no-referrer"
                onError={(e) => {
                  // Fallback styling if domain/port image is blocked
                  const target = e.currentTarget;
                  target.style.display = 'none';
                  if (target.parentElement) {
                    target.parentElement.innerHTML = `<span class="text-xs font-black text-slate-900 px-1 tracking-tight">LabCapital</span>`;
                  }
                }}
              />
            </div>

            <div className="min-w-0">
              <h1 className="font-extrabold text-white text-base sm:text-lg leading-tight tracking-tight truncate">
                Índice de Innovación Pública
              </h1>
              <p className="text-[11px] text-slate-400 font-medium hidden md:block truncate">
                Medición y Diagnóstico de Capacidades de Innovación
              </p>
            </div>
          </div>

          {/* Center Actions: Role Switcher & Entity Switcher */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            {/* High-Contrast Role Switcher */}
            <div className="bg-slate-950 p-1 rounded-2xl flex items-center border border-slate-800 text-xs shadow-inner">
              <button
                type="button"
                onClick={() => switchRole('admin')}
                className={`px-3 sm:px-4 py-1.5 rounded-xl font-bold transition-all flex items-center gap-1.5 ${
                  role === 'admin'
                    ? 'bg-amber-500 text-slate-950 shadow-md font-extrabold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <ShieldCheck className={`w-3.5 h-3.5 ${role === 'admin' ? 'text-slate-950' : 'text-amber-500'}`} />
                <span className="hidden sm:inline">Administración</span>
                <span className="sm:hidden">Admin</span>
              </button>

              <button
                type="button"
                onClick={() => switchRole('entity')}
                className={`px-3 sm:px-4 py-1.5 rounded-xl font-bold transition-all flex items-center gap-1.5 ${
                  role === 'entity'
                    ? 'bg-amber-500 text-slate-950 shadow-md font-extrabold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Building2 className={`w-3.5 h-3.5 ${role === 'entity' ? 'text-slate-950' : 'text-amber-500'}`} />
                <span className="hidden sm:inline">Entidades</span>
                <span className="sm:hidden">Entidad</span>
              </button>
            </div>

            {/* Quick Entity Switcher (When in entity mode) */}
            {role === 'entity' && (
              <div className="relative hidden lg:block">
                <button
                  type="button"
                  onClick={() => setShowEntityDropdown(!showEntityDropdown)}
                  className="px-3 py-1.5 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-xs font-semibold text-slate-200 flex items-center gap-2 transition-colors max-w-[220px]"
                >
                  <Building2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span className="truncate text-left">{activeActor?.label || 'Seleccionar Entidad'}</span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0 ml-auto" />
                </button>

                {showEntityDropdown && (
                  <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl p-2 z-50 animate-in fade-in">
                    <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-amber-400 border-b border-slate-800">
                      Entidades Distritales
                    </div>
                    <div className="max-h-64 overflow-y-auto py-1 space-y-1">
                      {actors.map((actor) => (
                        <button
                          key={actor.id}
                          onClick={() => {
                            switchEntity(actor.id, actor.label);
                            setShowEntityDropdown(false);
                          }}
                          className={`w-full text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between transition-colors ${
                            actor.id === activeActor?.id
                              ? 'bg-amber-500/10 text-amber-300 font-bold border border-amber-500/30'
                              : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                          }`}
                        >
                          <span className="truncate">{actor.label}</span>
                          {actor.actor_segment?.label && (
                            <span className="text-[10px] text-slate-500 shrink-0 ml-2">
                              {actor.actor_segment.label}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Tools: Settings & User Profile */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Settings */}
            <button
              onClick={onOpenSettings}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors border border-slate-800/80"
              title="Configuración de conectividad y endpoints"
            >
              <Settings className="w-4 h-4 text-slate-300" />
              <span className="hidden sm:inline">Configuración</span>
            </button>

            {/* Current User Pill */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 p-1 sm:px-2.5 sm:py-1 bg-slate-800 hover:bg-slate-700/80 border border-slate-700/80 rounded-2xl text-xs font-medium text-white transition-colors"
              >
                <div className="w-6 h-6 rounded-lg bg-amber-500 text-slate-950 font-black text-xs flex items-center justify-center shadow-xs">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="text-left hidden md:block">
                  <div className="font-bold text-xs leading-none text-slate-200 truncate max-w-[100px]">
                    {user?.username || 'usuario'}
                  </div>
                </div>
                <ChevronDown className="w-3 h-3 text-slate-400 hidden sm:block" />
              </button>

              {/* User Dropdown */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-60 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl p-2 z-50 animate-in fade-in">
                  <div className="p-3 border-b border-slate-800">
                    <div className="font-bold text-xs text-white">{user?.username}</div>
                    <div className="text-[11px] text-slate-400 truncate">{user?.email}</div>
                    <div className="mt-2 text-[10px] px-2 py-0.5 rounded bg-slate-800 text-amber-400 font-semibold inline-block">
                      {role === 'admin' ? 'Rol: Administrador Veeduría' : `Entidad: ${activeActor?.label}`}
                    </div>
                  </div>

                  <div className="py-1 space-y-1">
                    <button
                      onClick={() => {
                        onOpenSettings();
                        setShowUserMenu(false);
                      }}
                      className="w-full text-left px-3 py-2 rounded-xl text-xs text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2"
                    >
                      <Settings className="w-3.5 h-3.5 text-slate-400" />
                      <span>Configuración del Sistema</span>
                    </button>

                    <button
                      onClick={() => {
                        logout();
                        setShowUserMenu(false);
                      }}
                      className="w-full text-left px-3 py-2 rounded-xl text-xs text-rose-400 hover:bg-rose-950/40 flex items-center gap-2 border-t border-slate-800 mt-1"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Cerrar Sesión</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

