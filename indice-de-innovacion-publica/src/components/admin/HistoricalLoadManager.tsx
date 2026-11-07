import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  Loader2,
  Lock,
  LockOpen,
  RefreshCw,
  Upload,
  X,
} from 'lucide-react';
import { coreService } from '../../services/coreService';
import { HistoricalForm, HistoricalReport } from '../../types';

type Kind = 'responses' | 'results';

const KIND_LABEL: Record<Kind, string> = { responses: 'respuestas', results: 'resultados' };

const SUMMARY_LABEL: Record<string, string> = {
  entidades: 'Entidades',
  respuestas: 'Respuestas',
  tarjetas: 'Tarjetas',
  valores: 'Valores',
  reemplazos: 'Reemplazos',
};

const MAX_ROWS = 200;

/** Lleva el Blob descargado al disco del usuario. */
const saveBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

export const HistoricalLoadManager: React.FC = () => {
  const [forms, setForms] = useState<HistoricalForm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [upload, setUpload] = useState<{ form: HistoricalForm; kind: Kind } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setForms(await coreService.listHistoricalForms());
    } catch (err: any) {
      setError(err?.message || 'No se pudo cargar la lista de formularios.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const run = async (key: string, fn: () => Promise<void>) => {
    setBusy(key);
    setError(null);
    setNotice(null);
    try {
      await fn();
    } catch (err: any) {
      setError(err?.message || 'La operación no se pudo completar.');
    } finally {
      setBusy(null);
    }
  };

  const closeEdition = (f: HistoricalForm) => {
    if (
      !confirm(
        `¿Terminar la edición de «${f.label}»?\n\nLa estructura (componentes, variables, indicadores, preguntas y pesos) ya no se podrá modificar y se habilitarán las plantillas de carga histórica.`
      )
    )
      return;
    void run(`close-${f.id}`, async () => {
      await coreService.closeFormEdition(f.id);
      setNotice(`Edición de «${f.label}» terminada. Ya puede descargar las plantillas.`);
      await load();
    });
  };

  const reopenEdition = (f: HistoricalForm) => {
    if (!confirm(`¿Reabrir la edición de «${f.label}»? Las plantillas dejarán de estar disponibles hasta que la vuelva a cerrar.`))
      return;
    void run(`reopen-${f.id}`, async () => {
      await coreService.reopenFormEdition(f.id);
      setNotice(`Edición de «${f.label}» reabierta.`);
      await load();
    });
  };

  const download = (f: HistoricalForm, kind: Kind) =>
    run(`${kind}-${f.id}`, async () => {
      const { blob, filename } = await coreService.downloadHistoricalTemplate(f.id, kind);
      saveBlob(blob, filename);
    });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-indigo-600" />
            Cargas históricas
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-3xl leading-relaxed">
            Centralice en el servidor las mediciones anteriores. Cuando la estructura de un formulario esté lista,
            termine su edición: se habilitan dos plantillas Excel, una con las <strong>respuestas</strong> que dio cada
            entidad en su época y otra con sus <strong>resultados</strong> (puntaje por componente, variable e
            indicador, y total). Las entidades se identifican por su ID en la base de datos y los puntajes se guardan
            tal cual, sin validarlos contra los pesos.
          </p>
        </div>
        <button
          onClick={() => void load()}
          className="self-start px-3 py-2 text-xs font-semibold rounded-xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}
      {notice && (
        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-start gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{notice}</span>
        </div>
      )}

      <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-[10px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
              <th className="px-4 py-3 font-bold">Formulario</th>
              <th className="px-4 py-3 font-bold">Edición</th>
              <th className="px-4 py-3 font-bold text-right">Radicados</th>
              <th className="px-4 py-3 font-bold text-right">Resultados</th>
              <th className="px-4 py-3 font-bold">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {forms.map((f) => {
              const closed = !!f.edition_closed_at;
              const hasData = f.submission_count > 0 || f.result_count > 0;
              return (
                <tr key={f.id} className="align-top">
                  <td className="px-4 py-3">
                    <div className="font-bold text-slate-900">{f.label}</div>
                    <div className="text-[11px] text-slate-500 font-mono">
                      {f.code}
                      {f.year ? ` · ${f.year}` : ''}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {closed ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                        <Lock className="w-3 h-3" /> Terminada
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-amber-50 text-amber-700 border border-amber-200 font-semibold">
                        <LockOpen className="w-3 h-3" /> En edición
                      </span>
                    )}
                    {closed && (
                      <div className="text-[10px] text-slate-400 mt-1">
                        {new Date(f.edition_closed_at!).toLocaleDateString()}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{f.submission_count}</td>
                  <td className="px-4 py-3 text-right font-mono">{f.result_count}</td>
                  <td className="px-4 py-3">
                    {!closed ? (
                      <button
                        disabled={busy === `close-${f.id}`}
                        onClick={() => closeEdition(f)}
                        className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold flex items-center gap-1.5 disabled:opacity-60"
                      >
                        {busy === `close-${f.id}` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Lock className="w-3.5 h-3.5" />}
                        Terminar edición
                      </button>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {(['responses', 'results'] as Kind[]).map((kind) => (
                          <React.Fragment key={kind}>
                            <button
                              disabled={busy === `${kind}-${f.id}`}
                              onClick={() => void download(f, kind)}
                              className="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 font-semibold flex items-center gap-1.5 disabled:opacity-60"
                              title={`Descargar plantilla de ${KIND_LABEL[kind]}`}
                            >
                              {busy === `${kind}-${f.id}` ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <Download className="w-3.5 h-3.5" />
                              )}
                              Plantilla de {KIND_LABEL[kind]}
                            </button>
                            <button
                              onClick={() => setUpload({ form: f, kind })}
                              className="px-2.5 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold flex items-center gap-1.5"
                              title={`Cargar el Excel de ${KIND_LABEL[kind]}`}
                            >
                              <Upload className="w-3.5 h-3.5" />
                              Cargar {KIND_LABEL[kind]}
                            </button>
                          </React.Fragment>
                        ))}
                        <button
                          disabled={hasData || busy === `reopen-${f.id}`}
                          onClick={() => reopenEdition(f)}
                          title={hasData ? 'Ya tiene respuestas o resultados cargados: no se puede reabrir.' : 'Reabrir la edición'}
                          className="px-2.5 py-1.5 rounded-lg text-slate-500 hover:bg-slate-100 font-semibold flex items-center gap-1.5 disabled:opacity-40 disabled:hover:bg-transparent"
                        >
                          <LockOpen className="w-3.5 h-3.5" />
                          Reabrir edición
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
            {!loading && forms.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-slate-400">
                  No hay formularios en el servidor.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {upload && (
        <UploadModal
          form={upload.form}
          kind={upload.kind}
          onClose={() => setUpload(null)}
          onCommitted={async (msg) => {
            setNotice(msg);
            await load();
          }}
        />
      )}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Carga: validar el archivo y confirmar                               */
/* ------------------------------------------------------------------ */

const UploadModal: React.FC<{
  form: HistoricalForm;
  kind: Kind;
  onClose: () => void;
  onCommitted: (message: string) => Promise<void>;
}> = ({ form, kind, onClose, onCommitted }) => {
  const [file, setFile] = useState<File | null>(null);
  const [replace, setReplace] = useState(false);
  const [report, setReport] = useState<HistoricalReport | null>(null);
  const [working, setWorking] = useState<'validate' | 'commit' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  const reset = () => {
    setReport(null);
    setError(null);
  };

  const send = async (dryRun: boolean) => {
    if (!file) return;
    setWorking(dryRun ? 'validate' : 'commit');
    setError(null);
    try {
      const r = await coreService.uploadHistorical(form.id, kind, file, { dryRun, replace });
      setReport(r);
      if (r.committed) {
        setDone(true);
        const s = Object.entries(r.summary)
          .map(([k, v]) => `${v} ${(SUMMARY_LABEL[k] ?? k).toLowerCase()}`)
          .join(', ');
        await onCommitted(`Carga de ${KIND_LABEL[kind]} de «${form.label}» guardada: ${s}.`);
      }
    } catch (err: any) {
      setError(err?.message || 'No se pudo procesar el archivo.');
    } finally {
      setWorking(null);
    }
  };

  const valid = !!report && !report.committed && report.errors.length === 0;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-slate-100 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-slate-900">Cargar {KIND_LABEL[kind]} históricas</h2>
            <p className="text-xs text-slate-500">
              {form.label} <span className="font-mono">({form.code})</span>
            </p>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-4 text-xs">
          <div className="flex flex-wrap items-center gap-3">
            <input
              ref={input}
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setDone(false);
                reset();
              }}
            />
            <button
              onClick={() => input.current?.click()}
              disabled={done}
              className="px-3 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 font-semibold flex items-center gap-1.5 disabled:opacity-50"
            >
              <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
              {file ? 'Cambiar archivo' : 'Elegir archivo Excel (.xlsx)'}
            </button>
            {file && <span className="text-slate-600 font-mono truncate max-w-xs">{file.name}</span>}
          </div>

          {kind === 'responses' && (
            <label className="flex items-start gap-2 text-slate-700">
              <input
                type="checkbox"
                checked={replace}
                disabled={done}
                onChange={(e) => {
                  setReplace(e.target.checked);
                  reset();
                }}
                className="mt-0.5"
              />
              <span>
                Reemplazar las respuestas de las entidades que ya tengan un radicado de este formulario (incluye sus
                calificaciones). Sin marcar, esas entidades se reportan como error.
              </span>
            </label>
          )}

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {report && (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {Object.entries(report.summary).map(([k, v]) => (
                  <span key={k} className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-semibold">
                    {SUMMARY_LABEL[k] ?? k}: <span className="font-mono">{v}</span>
                  </span>
                ))}
              </div>

              {report.committed && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center gap-2 font-semibold">
                  <CheckCircle2 className="w-4 h-4" /> Carga guardada en el servidor.
                </div>
              )}
              {valid && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center gap-2 font-semibold">
                  <CheckCircle2 className="w-4 h-4" /> El archivo es válido. Aún no se ha guardado nada.
                </div>
              )}
              {report.errors.length > 0 && (
                <IssueTable
                  tone="error"
                  title={`${report.errors.length} error(es): no se guardó nada`}
                  issues={report.errors}
                />
              )}
              {report.warnings.length > 0 && (
                <IssueTable tone="warning" title={`${report.warnings.length} aviso(s)`} issues={report.warnings} />
              )}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-slate-100 flex flex-wrap justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-semibold text-xs">
            {done ? 'Cerrar' : 'Cancelar'}
          </button>
          {!done && (
            <>
              <button
                disabled={!file || !!working}
                onClick={() => void send(true)}
                className="px-4 py-2 rounded-xl border border-indigo-200 text-indigo-700 hover:bg-indigo-50 font-semibold text-xs flex items-center gap-1.5 disabled:opacity-50"
              >
                {working === 'validate' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Validar archivo
              </button>
              <button
                disabled={!valid || !!working}
                onClick={() => void send(false)}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs flex items-center gap-1.5 disabled:opacity-50"
              >
                {working === 'commit' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Confirmar carga
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const IssueTable: React.FC<{
  tone: 'error' | 'warning';
  title: string;
  issues: HistoricalReport['errors'];
}> = ({ tone, title, issues }) => {
  const color =
    tone === 'error'
      ? 'bg-rose-50 border-rose-200 text-rose-800'
      : 'bg-amber-50 border-amber-200 text-amber-800';
  return (
    <div className={`rounded-xl border ${color} overflow-hidden`}>
      <div className="px-3 py-2 font-bold">{title}</div>
      <div className="max-h-64 overflow-y-auto bg-white/70">
        <table className="w-full text-[11px] text-slate-700">
          <thead>
            <tr className="text-left text-slate-400">
              <th className="px-3 py-1.5 font-semibold">Hoja</th>
              <th className="px-3 py-1.5 font-semibold">Fila</th>
              <th className="px-3 py-1.5 font-semibold">Columna</th>
              <th className="px-3 py-1.5 font-semibold">Detalle</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {issues.slice(0, MAX_ROWS).map((i, idx) => (
              <tr key={idx}>
                <td className="px-3 py-1.5 font-mono">{i.sheet}</td>
                <td className="px-3 py-1.5 font-mono">{i.row ?? '—'}</td>
                <td className="px-3 py-1.5 font-mono">{i.column ?? '—'}</td>
                <td className="px-3 py-1.5">{i.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {issues.length > MAX_ROWS && (
          <div className="px-3 py-2 text-slate-500">… y {issues.length - MAX_ROWS} más. Corrija estos y vuelva a validar.</div>
        )}
      </div>
    </div>
  );
};
