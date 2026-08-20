import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { apiClient } from '../../services/apiClient';
import {
  Settings,
  X,
  Server,
  Shield,
  RefreshCw,
  Database,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sliders,
  Terminal,
  Box,
} from 'lucide-react';

interface ApiSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenLogs?: () => void;
  onOpenDocker?: () => void;
}

export const ApiSettingsModal: React.FC<ApiSettingsModalProps> = ({
  isOpen,
  onClose,
  onOpenLogs,
  onOpenDocker,
}) => {
  const { config, updateConfig, resetAllMockData } = useApp();
  const { reauth, isAuthenticated } = useAuth();

  const [authUrl, setAuthUrl] = useState(config.authBaseUrl);
  const [coreUrl, setCoreUrl] = useState(config.coreBaseUrl);
  const [platform, setPlatform] = useState(config.platform);
  const [useRealBackend, setUseRealBackend] = useState(config.useRealBackend);
  const [isReauthing, setIsReauthing] = useState(false);
  const [reauthMsg, setReauthMsg] = useState<{ text: string; success: boolean } | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSave = () => {
    updateConfig({
      authBaseUrl: authUrl.trim(),
      coreBaseUrl: coreUrl.trim(),
      platform,
      useRealBackend,
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  const handleTestReauth = async () => {
    setIsReauthing(true);
    setReauthMsg(null);
    try {
      await reauth();
      setReauthMsg({ text: 'Token JWT Ed25519 rotado exitosamente (/public/auth/reauth).', success: true });
    } catch (err: any) {
      setReauthMsg({
        text: err?.message || 'Error en reautenticación.',
        success: false,
      });
    } finally {
      setIsReauthing(false);
    }
  };

  const tokens = apiClient.getTokens();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-50 text-indigo-700 rounded-lg">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-base">Configuración de Conexión & API</h3>
              <p className="text-xs text-slate-500">Parámetros del backend FastAPI y autenticación Ed25519</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm">
          {/* Mode Selector */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium text-slate-900 block">Modo de Operación</span>
                <span className="text-xs text-slate-500">
                  Alternar entre datos locales enriquecidos y llamadas HTTP a los microservicios FastAPI.
                </span>
              </div>
              <button
                onClick={() => setUseRealBackend(!useRealBackend)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  useRealBackend ? 'bg-indigo-600' : 'bg-slate-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    useRealBackend ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center gap-2 pt-1 text-xs">
              <span
                className={`px-2.5 py-1 rounded-md font-medium flex items-center gap-1.5 ${
                  useRealBackend
                    ? 'bg-indigo-100 text-indigo-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                {useRealBackend ? 'Modo Backend Real (FastAPI Activo)' : 'Modo Local (Datos de Prueba Mock Activos)'}
              </span>
            </div>
          </div>

          {/* Endpoints Form */}
          <div className="space-y-4">
            <h4 className="font-medium text-slate-900 flex items-center gap-2 text-xs uppercase tracking-wider text-slate-500">
              <Server className="w-4 h-4" /> Endpoints de los Microservicios
            </h4>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Auth Service Base URL (/public/auth/*)
              </label>
              <input
                type="text"
                value={authUrl}
                onChange={(e) => setAuthUrl(e.target.value)}
                placeholder="http://localhost:4293"
                className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Utilizado para login, register, reauth y logout.
              </p>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Core Service Base URL (/public/*)
              </label>
              <input
                type="text"
                value={coreUrl}
                onChange={(e) => setCoreUrl(e.target.value)}
                placeholder="http://localhost:4294"
                className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Utilizado para /actors, /actor_segments, /forms y /submissions.
              </p>
            </div>
          </div>

          {/* Header X-Platform Selection */}
          <div className="space-y-3 pt-2 border-t border-slate-100">
            <h4 className="font-medium text-slate-900 flex items-center gap-2 text-xs uppercase tracking-wider text-slate-500">
              <Shield className="w-4 h-4" /> Header Obligatorio: X-Platform
            </h4>

            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setPlatform('mobile')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  platform === 'mobile'
                    ? 'border-indigo-600 bg-indigo-50/50 ring-1 ring-indigo-600 text-indigo-950'
                    : 'border-slate-200 hover:border-slate-300 text-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-xs">mobile (Recomendado en Dev)</span>
                  {platform === 'mobile' && <CheckCircle2 className="w-4 h-4 text-indigo-600" />}
                </div>
                <p className="text-[11px] text-slate-500">
                  Refresh token viaja en body y se envía en header X-Refresh-Token. Compatible con CORS en desarrollo.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setPlatform('web')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  platform === 'web'
                    ? 'border-indigo-600 bg-indigo-50/50 ring-1 ring-indigo-600 text-indigo-950'
                    : 'border-slate-200 hover:border-slate-300 text-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-xs">web (Producción Cookies)</span>
                  {platform === 'web' && <CheckCircle2 className="w-4 h-4 text-indigo-600" />}
                </div>
                <p className="text-[11px] text-slate-500">
                  Refresh token viaja en cookie httpOnly (requiere allow_credentials=True y mismo origen/dominio).
                </p>
              </button>
            </div>
          </div>

          {/* Tokens status & Rotation */}
          <div className="space-y-3 pt-2 border-t border-slate-100">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-slate-900 flex items-center gap-2 text-xs uppercase tracking-wider text-slate-500">
                <Sliders className="w-4 h-4" /> Estado de Tokens JWT (Ed25519)
              </h4>
              {isAuthenticated && (
                <button
                  onClick={handleTestReauth}
                  disabled={isReauthing}
                  className="px-2.5 py-1 text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isReauthing ? 'animate-spin' : ''}`} />
                  Rotar Token (/reauth)
                </button>
              )}
            </div>

            {reauthMsg && (
              <div
                className={`p-2.5 rounded-lg text-xs flex items-center gap-2 ${
                  reauthMsg.success ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'
                }`}
              >
                {reauthMsg.success ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                {reauthMsg.text}
              </div>
            )}

            <div className="bg-slate-900 text-slate-200 p-3 rounded-xl font-mono text-[11px] space-y-1.5 overflow-x-auto">
              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">access_token (30 min):</span>
                <span className="text-emerald-400 truncate max-w-[280px]">
                  {tokens.accessToken || 'null (No autenticado)'}
                </span>
              </div>
              <div className="flex justify-between pt-1">
                <span className="text-slate-400">refresh_token (7 días):</span>
                <span className="text-indigo-300 truncate max-w-[280px]">
                  {tokens.refreshToken || (platform === 'web' ? 'Gestionado en cookie httpOnly' : 'null')}
                </span>
              </div>
            </div>
          </div>

          {/* Diagnostics and Reset */}
          <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
            <button
              onClick={() => {
                if (confirm('¿Restablecer todos los datos de prueba a los valores iniciales predeterminados?')) {
                  resetAllMockData();
                  alert('Datos restablecidos.');
                }
              }}
              className="text-xs text-slate-500 hover:text-rose-600 flex items-center gap-1.5 py-1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Restablecer Datos Locales de Prueba
            </button>

            <div className="flex items-center gap-3">
              {onOpenDocker && (
                <button
                  onClick={() => {
                    onClose();
                    onOpenDocker();
                  }}
                  className="text-xs text-amber-700 hover:text-amber-800 flex items-center gap-1.5 py-1 font-semibold"
                >
                  <Box className="w-3.5 h-3.5" />
                  Docker & YAML
                </button>
              )}

              {onOpenLogs && (
                <button
                  onClick={() => {
                    onClose();
                    onOpenLogs();
                  }}
                  className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1.5 py-1 font-medium"
                >
                  <Terminal className="w-3.5 h-3.5" />
                  Ver Consola de Logs HTTP
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <div>
            {savedSuccess && (
              <span className="text-xs font-medium text-emerald-700 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Cambios aplicados
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
            >
              Cerrar
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-xs transition-colors"
            >
              Guardar Configuración
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
