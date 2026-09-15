import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import {
  Server,
  Play,
  Send,
  Code2,
  Clock,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Globe,
  Lock,
  Key,
} from 'lucide-react';

export const ApiTesterConsole: React.FC = () => {
  const { config, logHttpTransaction } = useApp();
  const { accessToken, refreshToken, platformHeader } = useAuth();

  const [service, setService] = useState<'auth' | 'core'>('core');
  const [method, setMethod] = useState<'GET' | 'POST' | 'DELETE' | 'PUT'>('GET');
  const [endpoint, setEndpoint] = useState('/actors/all');
  const [requestBody, setRequestBody] = useState('{\n  \n}');
  const [includeAuth, setIncludeAuth] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [responseStatus, setResponseStatus] = useState<number | null>(null);
  const [responseData, setResponseData] = useState<any | null>(null);
  const [responseHeaders, setResponseHeaders] = useState<Record<string, string>>({});
  const [copied, setCopied] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);

  const presets = [
    { label: 'GET /actors/all', service: 'core', method: 'GET', endpoint: '/actors/all', body: '' },
    { label: 'GET /actor_segments/all', service: 'core', method: 'GET', endpoint: '/actor_segments/all', body: '' },
    {
      label: 'POST /actors/new',
      service: 'core',
      method: 'POST',
      endpoint: '/actors/new',
      body: JSON.stringify(
        {
          label: 'Secretaría de Hábitat y Urbanismo',
          description: 'Entidad encargada del desarrollo territorial',
          actor_segment_id: null,
        },
        null,
        2
      ),
    },
    {
      label: 'POST /auth/login',
      service: 'auth',
      method: 'POST',
      endpoint: '/auth/login',
      body: JSON.stringify(
        {
          username: 'admin@bogota.gov.co',
          password: 'Password123!',
        },
        null,
        2
      ),
    },
    {
      label: 'POST /auth/reauth',
      service: 'auth',
      method: 'POST',
      endpoint: '/auth/reauth',
      body: '',
    },
  ];

  const handleApplyPreset = (p: (typeof presets)[0]) => {
    setService(p.service as any);
    setMethod(p.method as any);
    setEndpoint(p.endpoint);
    setRequestBody(p.body || '{\n  \n}');
  };

  const handleExecuteRequest = async () => {
    setIsLoading(true);
    setResponseStatus(null);
    setResponseData(null);
    const baseUrl = service === 'auth' ? config.authServiceUrl : config.coreServiceUrl;
    const fullUrl = `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Platform': platformHeader,
    };

    if (includeAuth && accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    if (endpoint === '/auth/reauth' || endpoint === '/auth/logout') {
      if (refreshToken) {
        headers['X-Refresh-Token'] = refreshToken;
      }
    }

    const startTime = Date.now();
    try {
      const response = await fetch(fullUrl, {
        method,
        headers,
        body: method !== 'GET' && method !== 'HEAD' && requestBody.trim() ? requestBody : undefined,
      });

      const elapsed = Date.now() - startTime;
      setLatency(elapsed);
      setResponseStatus(response.status);

      const resHeaders: Record<string, string> = {};
      response.headers.forEach((val, key) => {
        resHeaders[key] = val;
      });
      setResponseHeaders(resHeaders);

      let parsedData: any;
      try {
        parsedData = await response.json();
      } catch {
        parsedData = await response.text();
      }
      setResponseData(parsedData);

      logHttpTransaction({
        method,
        url: fullUrl,
        headers,
        requestBody: method !== 'GET' ? requestBody : undefined,
        responseStatus: response.status,
        responseBody: parsedData,
        durationMs: elapsed,
      });
    } catch (err: any) {
      const elapsed = Date.now() - startTime;
      setLatency(elapsed);
      setResponseStatus(0);
      const errorObj = {
        error: 'NetworkError / Connection Refused',
        message: err?.message || 'Failed to fetch',
        detail:
          'Asegúrese de que el backend FastAPI esté corriendo y que acepte certificados autofirmados si usa HTTPS (https://localhost:4293/4294)',
      };
      setResponseData(errorObj);

      logHttpTransaction({
        method,
        url: fullUrl,
        headers,
        requestBody: method !== 'GET' ? requestBody : undefined,
        responseStatus: 0,
        responseBody: errorObj,
        durationMs: elapsed,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyResponse = () => {
    navigator.clipboard.writeText(JSON.stringify(responseData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
              Herramienta de Diagnóstico Backend
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-indigo-50 text-indigo-700 font-bold">
              FastAPI Interactive Client
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mt-0.5">Consola de Pruebas de API</h2>
          <p className="text-xs text-slate-500">
            Realice peticiones HTTP directas hacia los microservicios de Autenticación (4293) y Core (4294)
            con tokens JWT Ed25519 y headers de plataforma.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`text-xs px-3 py-1.5 rounded-xl font-semibold border ${
              config.useRealBackend
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}
          >
            Modo: {config.useRealBackend ? 'Backend Real Conectado' : 'Simulador / Mock UI'}
          </span>
        </div>
      </div>

      {/* Presets Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-2">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
          Plantillas Rápidas de Endpoints
        </span>
        <div className="flex flex-wrap gap-2">
          {presets.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleApplyPreset(p)}
              className="px-3 py-1.5 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 rounded-xl text-xs font-mono font-medium transition-colors"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Request Composer */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Request Configuration */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-5">
          <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
            <Server className="w-4 h-4 text-indigo-600" />
            Configuración de la Petición
          </h3>

          {/* Service & Method */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Servicio Destino</label>
              <select
                value={service}
                onChange={(e) => setService(e.target.value as any)}
                className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
              >
                <option value="auth">Auth Service ({config.authServiceUrl})</option>
                <option value="core">Core Service ({config.coreServiceUrl})</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Método HTTP</label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as any)}
                className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-bold focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
              </select>
            </div>
          </div>

          {/* Endpoint */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Ruta del Endpoint</label>
            <div className="flex items-center">
              <span className="px-3 py-2 bg-slate-100 border border-r-0 border-slate-300 rounded-l-xl text-xs font-mono text-slate-500">
                {service === 'auth' ? ':4293' : ':4294'}
              </span>
              <input
                type="text"
                value={endpoint}
                onChange={(e) => setEndpoint(e.target.value)}
                placeholder="/actors/all"
                className="w-full px-3 py-2 border border-slate-300 rounded-r-xl text-xs font-mono focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
          </div>

          {/* Headers preview & options */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-700">Headers Automáticos</span>
              <label className="flex items-center gap-1.5 text-[11px] text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeAuth}
                  onChange={(e) => setIncludeAuth(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span>Enviar Authorization: Bearer</span>
              </label>
            </div>
            <div className="font-mono text-[11px] text-slate-600 space-y-1">
              <div>
                <span className="text-slate-400">X-Platform:</span> {platformHeader}
              </div>
              <div>
                <span className="text-slate-400">Content-Type:</span> application/json
              </div>
              {includeAuth && (
                <div className="truncate">
                  <span className="text-slate-400">Authorization:</span> Bearer{' '}
                  {accessToken ? `${accessToken.slice(0, 20)}...` : '(No hay token en sesión)'}
                </div>
              )}
            </div>
          </div>

          {/* Body editor */}
          {method !== 'GET' && method !== 'HEAD' && (
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Cuerpo JSON (Body)</label>
              <textarea
                rows={6}
                value={requestBody}
                onChange={(e) => setRequestBody(e.target.value)}
                className="w-full p-3 font-mono text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none bg-slate-950 text-emerald-400"
              />
            </div>
          )}

          {/* Send Button */}
          <button
            onClick={handleExecuteRequest}
            disabled={isLoading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span>Ejecutar Petición HTTP</span>
          </button>
        </div>

        {/* Right: Response Inspector */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 flex flex-col justify-between space-y-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Code2 className="w-4 h-4 text-indigo-600" />
                Respuesta del Servidor
              </h3>

              {responseStatus !== null && (
                <div className="flex items-center gap-2">
                  {latency && (
                    <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {latency}ms
                    </span>
                  )}
                  <span
                    className={`px-2.5 py-0.5 rounded-full font-mono text-xs font-bold ${
                      responseStatus >= 200 && responseStatus < 300
                        ? 'bg-emerald-100 text-emerald-800'
                        : responseStatus === 0
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    HTTP {responseStatus === 0 ? 'FAIL' : responseStatus}
                  </span>
                </div>
              )}
            </div>

            {responseData ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>Cuerpo de Respuesta (JSON)</span>
                  <button
                    onClick={handleCopyResponse}
                    className="text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1"
                  >
                    {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copiado' : 'Copiar'}</span>
                  </button>
                </div>

                <pre className="p-4 bg-slate-950 text-emerald-400 font-mono text-xs rounded-xl overflow-x-auto max-h-[380px]">
                  {JSON.stringify(responseData, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="h-64 border-2 border-dashed border-slate-200 rounded-2xl flex flex-col items-center justify-center text-center p-6 text-slate-400 space-y-2">
                <Globe className="w-8 h-8 opacity-40" />
                <p className="text-xs">Configure la petición y haga clic en "Ejecutar Petición HTTP".</p>
              </div>
            )}
          </div>

          <div className="text-[11px] text-slate-400 border-t border-slate-100 pt-3 flex items-center justify-between">
            <span>JWT Ed25519 activo</span>
            <span>X-Platform: {platformHeader}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
