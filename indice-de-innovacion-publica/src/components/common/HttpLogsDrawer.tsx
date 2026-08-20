import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { HttpLog } from '../../types';
import {
  Terminal,
  X,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowUpRight,
  Filter,
  Copy,
  Check,
} from 'lucide-react';

interface HttpLogsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HttpLogsDrawer: React.FC<HttpLogsDrawerProps> = ({ isOpen, onClose }) => {
  const { logs, clearLogs, config } = useApp();
  const [selectedLog, setSelectedLog] = useState<HttpLog | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [filterMode, setFilterMode] = useState<'all' | 'real' | 'mock'>('all');

  if (!isOpen) return null;

  const filteredLogs = logs.filter((log) => {
    if (filterMode === 'all') return true;
    return log.mode === filterMode;
  });

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/50 backdrop-blur-xs">
      <div className="bg-slate-950 text-slate-100 w-full max-w-3xl h-full shadow-2xl flex flex-col border-l border-slate-800 animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-500/20 text-indigo-400 rounded-lg">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-white text-base">Consola de Tráfico HTTP & API</h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-indigo-900/60 text-indigo-300 border border-indigo-700/50">
                  {logs.length} peticiones
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Inspección de requests, headers X-Platform, tokens Ed25519 y respuestas FastAPI
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={clearLogs}
              title="Limpiar historial"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="px-5 py-2.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400 font-medium">Filtrar:</span>
            <div className="inline-flex rounded-lg bg-slate-950 p-0.5 border border-slate-800">
              <button
                onClick={() => setFilterMode('all')}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  filterMode === 'all' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Todos ({logs.length})
              </button>
              <button
                onClick={() => setFilterMode('real')}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  filterMode === 'real' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                FastAPI Real ({logs.filter((l) => l.mode === 'real').length})
              </button>
              <button
                onClick={() => setFilterMode('mock')}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  filterMode === 'mock' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Mock Local ({logs.filter((l) => l.mode === 'mock').length})
              </button>
            </div>
          </div>

          <div className="text-[11px] font-mono text-slate-400 flex items-center gap-2">
            <span>Auth: {config.authBaseUrl}</span>
            <span>•</span>
            <span>Core: {config.coreBaseUrl}</span>
          </div>
        </div>

        {/* Content: Master / Detail */}
        <div className="flex-1 flex overflow-hidden">
          {/* Logs List */}
          <div className="w-1/2 border-r border-slate-800 overflow-y-auto divide-y divide-slate-800/60">
            {filteredLogs.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                No hay peticiones registradas aún en este filtro.
              </div>
            ) : (
              filteredLogs.map((log) => {
                const isSelected = selectedLog?.id === log.id;
                const isOk = log.status >= 200 && log.status < 300;
                const isError = log.status >= 400 || log.status === 0;

                return (
                  <button
                    key={log.id}
                    onClick={() => setSelectedLog(log)}
                    className={`w-full text-left p-3.5 transition-colors block ${
                      isSelected ? 'bg-indigo-950/70 border-l-2 border-indigo-500' : 'hover:bg-slate-900/60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            log.method === 'GET'
                              ? 'bg-sky-900/80 text-sky-300'
                              : log.method === 'POST'
                              ? 'bg-emerald-900/80 text-emerald-300'
                              : log.method === 'DELETE'
                              ? 'bg-rose-900/80 text-rose-300'
                              : 'bg-amber-900/80 text-amber-300'
                          }`}
                        >
                          {log.method}
                        </span>
                        <span
                          className={`font-mono text-[11px] font-bold ${
                            isOk ? 'text-emerald-400' : isError ? 'text-rose-400' : 'text-slate-300'
                          }`}
                        >
                          {log.status === 0 ? 'ERR' : log.status}
                        </span>
                        <span
                          className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                            log.mode === 'real'
                              ? 'bg-purple-900/60 text-purple-300'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {log.mode}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 flex items-center gap-1 font-mono">
                        <Clock className="w-2.5 h-2.5" />
                        {log.durationMs}ms
                      </span>
                    </div>

                    <div className="font-mono text-xs text-slate-200 truncate mt-1">{log.url}</div>
                    <div className="text-[10px] text-slate-500 mt-1">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Log Detail Inspector */}
          <div className="w-1/2 overflow-y-auto p-4 space-y-4 bg-slate-950 font-mono text-xs">
            {selectedLog ? (
              <>
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white">{selectedLog.method}</span>
                    <span
                      className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                        selectedLog.status >= 200 && selectedLog.status < 300
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : 'bg-rose-950 text-rose-300 border border-rose-800'
                      }`}
                    >
                      Status {selectedLog.status}
                    </span>
                  </div>
                  <button
                    onClick={() => handleCopy(JSON.stringify(selectedLog, null, 2), selectedLog.id)}
                    className="p-1 text-slate-400 hover:text-white rounded bg-slate-900 hover:bg-slate-800 transition-colors flex items-center gap-1 text-[11px]"
                  >
                    {copiedId === selectedLog.id ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                    <span>{copiedId === selectedLog.id ? 'Copiado' : 'Copiar JSON'}</span>
                  </button>
                </div>

                <div>
                  <span className="text-slate-400 text-[11px] block mb-1 uppercase font-semibold">URL Completa</span>
                  <div className="p-2 bg-slate-900 rounded border border-slate-800 text-slate-200 break-all select-all">
                    {selectedLog.url}
                  </div>
                </div>

                <div>
                  <span className="text-slate-400 text-[11px] block mb-1 uppercase font-semibold">
                    Headers Enviados (X-Platform, Auth)
                  </span>
                  <div className="p-2 bg-slate-900 rounded border border-slate-800 text-slate-300 space-y-1">
                    {Object.entries(selectedLog.headers).map(([k, v]) => (
                      <div key={k} className="flex gap-2">
                        <span className="text-indigo-300 font-semibold">{k}:</span>
                        <span className="text-slate-400 break-all">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {selectedLog.body && (
                  <div>
                    <span className="text-slate-400 text-[11px] block mb-1 uppercase font-semibold">
                      Request Body (JSON)
                    </span>
                    <pre className="p-2.5 bg-slate-900 rounded border border-slate-800 text-emerald-300 overflow-x-auto text-[11px]">
                      {JSON.stringify(selectedLog.body, null, 2)}
                    </pre>
                  </div>
                )}

                <div>
                  <span className="text-slate-400 text-[11px] block mb-1 uppercase font-semibold">
                    Response Payload (FastAPI)
                  </span>
                  <pre className="p-2.5 bg-slate-900 rounded border border-slate-800 text-sky-300 overflow-x-auto text-[11px]">
                    {typeof selectedLog.response === 'object'
                      ? JSON.stringify(selectedLog.response, null, 2)
                      : String(selectedLog.response)}
                  </pre>
                </div>
              </>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 p-6">
                <Terminal className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                <p>Selecciona una petición de la lista para inspeccionar encabezados, cuerpo y respuesta.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
