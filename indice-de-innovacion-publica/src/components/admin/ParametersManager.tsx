import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, Loader2, Lock, Pencil, Plus, Search, Trash2, X } from 'lucide-react';
import { ParamColumn, ParamRow, ParamTable, parametersService } from '../../services/parametersService';
import { ROUTES, navigate } from '../../utils/router';
import { useApp } from '../../context/AppContext';

const MB = 1024 * 1024;
const inputCls =
  'w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:outline-hidden focus:border-amber-500 focus:ring-1 focus:ring-amber-500 disabled:bg-slate-100 disabled:text-slate-500';

const formatBytes = (n: number) => (n >= MB ? `${+(n / MB).toFixed(2)} MB` : `${Math.round(n / 1024)} KB`);

const cellText = (col: ParamColumn, v: any) => {
  if (v === null || v === undefined || v === '') return '—';
  if (col.unit === 'bytes') return formatBytes(Number(v));
  if (col.type === 'boolean') return v ? 'Sí' : 'No';
  return String(v);
};

/** Formulario genérico (crear/editar) generado a partir de las columnas del catálogo. */
const RowModal: React.FC<{
  table: ParamTable;
  row: ParamRow | null;
  onClose: () => void;
  onSaved: () => void;
}> = ({ table, row, onClose, onSaved }) => {
  const editing = !!row;
  const [values, setValues] = useState<Record<string, any>>(() => {
    const v: Record<string, any> = {};
    for (const c of table.columns) v[c.name] = row ? (row[c.name] ?? '') : '';
    return v;
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    setError(null);
    try {
      const body: Record<string, any> = {};
      for (const c of table.columns) {
        if (editing && c.locked_on_edit) continue;
        body[c.name] = values[c.name];
      }
      if (editing) await parametersService.update(table.key, row!.id, body);
      else await parametersService.create(table.key, body);
      onSaved();
    } catch (err: any) {
      setError(err?.message || 'No se pudo guardar.');
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/70 flex items-center justify-center p-4 overflow-y-auto">
      <form onSubmit={submit} className="relative bg-white w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        {saving && (
          <div className="absolute inset-0 z-10 bg-white/80 flex items-center justify-center cursor-wait">
            <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
          </div>
        )}
        <div className="bg-slate-900 text-white px-5 py-3 flex items-center justify-between">
          <h3 className="font-bold text-sm">
            {editing ? 'Editar' : 'Nuevo'} — {table.label}
          </h3>
          <button type="button" onClick={onClose} disabled={saving} className="p-1 text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-3 max-h-[70vh] overflow-y-auto">
          {table.columns.map((c) => {
            const locked = editing && c.locked_on_edit;
            return (
              <div key={c.name}>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                  {c.label}
                  {c.unit === 'bytes' ? ' (MB)' : ''} {c.required && <span className="text-amber-600">*</span>}
                  {locked && (
                    <span className="ml-2 inline-flex items-center gap-0.5 text-slate-400 font-normal">
                      <Lock className="w-3 h-3" /> no editable
                    </span>
                  )}
                </label>
                {c.type === 'textarea' ? (
                  <textarea
                    className={`${inputCls} min-h-[70px]`}
                    value={values[c.name] ?? ''}
                    disabled={locked}
                    onChange={(e) => setValues({ ...values, [c.name]: e.target.value })}
                  />
                ) : c.type === 'boolean' ? (
                  <input
                    type="checkbox"
                    checked={!!values[c.name]}
                    disabled={locked}
                    onChange={(e) => setValues({ ...values, [c.name]: e.target.checked })}
                  />
                ) : c.unit === 'bytes' ? (
                  <input
                    type="number"
                    min={0}
                    step="any"
                    className={inputCls}
                    disabled={locked}
                    value={values[c.name] === '' ? '' : +(Number(values[c.name]) / MB).toFixed(4)}
                    onChange={(e) =>
                      setValues({ ...values, [c.name]: e.target.value === '' ? '' : Math.round(Number(e.target.value) * MB) })
                    }
                  />
                ) : c.type === 'integer' || c.type === 'number' ? (
                  <input
                    type="number"
                    min={0}
                    className={inputCls}
                    disabled={locked}
                    value={values[c.name] ?? ''}
                    onChange={(e) => setValues({ ...values, [c.name]: e.target.value })}
                  />
                ) : (
                  <input
                    className={inputCls}
                    maxLength={c.max_length ?? undefined}
                    disabled={locked}
                    value={values[c.name] ?? ''}
                    onChange={(e) => setValues({ ...values, [c.name]: e.target.value })}
                  />
                )}
              </div>
            );
          })}
          {error && (
            <div className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </div>
        <div className="px-5 py-3 border-t border-slate-200 flex justify-end gap-2 bg-slate-50">
          <button type="button" onClick={onClose} disabled={saving} className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl">
            Cancelar
          </button>
          <button type="submit" disabled={saving} className="px-5 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-extrabold rounded-xl disabled:opacity-50">
            {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </div>
      </form>
    </div>
  );
};

export const ParametersManager: React.FC<{ pathname: string }> = ({ pathname }) => {
  const { refreshData } = useApp();
  const [tables, setTables] = useState<ParamTable[]>([]);
  const [rows, setRows] = useState<ParamRow[]>([]);
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [loadingRows, setLoadingRows] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState<{ row: ParamRow | null } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const keyFromPath = pathname.split('/')[3];
  const table = tables.find((t) => t.key === keyFromPath) ?? tables[0];

  useEffect(() => {
    parametersService
      .catalog()
      .then(setTables)
      .catch((e) => setError(e?.message || 'No se pudo cargar el catálogo de parámetros.'))
      .finally(() => setLoadingCatalog(false));
  }, []);

  // Normaliza la URL a /admin/parametros/<tabla>
  useEffect(() => {
    if (table && keyFromPath !== table.key) navigate(`${ROUTES.admin.parameters}/${table.key}`, { replace: true });
  }, [table, keyFromPath]);

  const loadRows = useCallback(async () => {
    if (!table) return;
    setLoadingRows(true);
    setError(null);
    try {
      setRows(await parametersService.list(table.key));
    } catch (e: any) {
      setError(e?.message || 'No se pudieron cargar los registros.');
    } finally {
      setLoadingRows(false);
    }
  }, [table?.key]);

  useEffect(() => {
    setSearch('');
    setRows([]);
    loadRows();
  }, [loadRows]);

  const groups = useMemo(() => {
    const g: Record<string, ParamTable[]> = {};
    tables.forEach((t) => (g[t.group] ??= []).push(t));
    return g;
  }, [tables]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => Object.values(r).some((v) => String(v ?? '').toLowerCase().includes(q)));
  }, [rows, search]);

  const afterChange = async () => {
    setModal(null);
    await loadRows();
    if (table?.key === 'sectores') refreshData(); // la pantalla de Entidades usa los sectores
  };

  const remove = async (r: ParamRow) => {
    if (!table || busyId) return;
    if (!confirm(`¿Eliminar "${r.label ?? r.code ?? r.key}"?`)) return;
    setBusyId(r.id);
    try {
      await parametersService.remove(table.key, r.id);
      await afterChange();
    } catch (e: any) {
      alert(e?.message || 'No se pudo eliminar.');
    } finally {
      setBusyId(null);
    }
  };

  if (loadingCatalog)
    return (
      <div className="p-10 flex items-center gap-3 text-slate-500 text-sm">
        <Loader2 className="w-5 h-5 animate-spin text-amber-500" /> Cargando parámetros…
      </div>
    );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div>
        <span className="text-[11px] font-bold text-amber-600 uppercase tracking-wider bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
          Administración • Parámetros
        </span>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">Parámetros del sistema</h2>
        <p className="text-xs text-slate-500">
          Listas y catálogos que alimentan los formularios y la plataforma, administrables sin tocar la base de datos.
        </p>
      </div>

      {error && !table && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800">{error}</div>
      )}

      {table && (
        <div className="grid grid-cols-1 lg:grid-cols-[16rem_1fr] gap-6">
          <nav className="space-y-4">
            {(Object.entries(groups) as [string, ParamTable[]][]).map(([group, items]) => (
              <div key={group}>
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 px-2">{group}</div>
                <div className="space-y-0.5">
                  {items.map((t) => (
                    <a
                      key={t.key}
                      href={`${ROUTES.admin.parameters}/${t.key}`}
                      onClick={(e) => {
                        e.preventDefault();
                        navigate(`${ROUTES.admin.parameters}/${t.key}`);
                      }}
                      className={`block px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                        t.key === table.key ? 'bg-slate-900 text-amber-400' : 'text-slate-600 hover:bg-slate-200/60'
                      }`}
                    >
                      {t.label}
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </nav>

          <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">{table.label}</h3>
                <p className="text-[11px] text-slate-500">{table.description}</p>
                {!table.can_create && (
                  <p className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1">
                    <Lock className="w-3 h-3" /> Catálogo base: solo se pueden editar los textos (el código tiene lógica en el sistema).
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    className={`${inputCls} !pl-8 !w-48`}
                    placeholder="Buscar…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
                {table.can_create && (
                  <button
                    onClick={() => setModal({ row: null })}
                    className="px-3.5 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-extrabold rounded-xl flex items-center gap-1.5"
                  >
                    <Plus className="w-4 h-4" /> Nuevo
                  </button>
                )}
              </div>
            </div>

            {error && <div className="m-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800">{error}</div>}

            <div className="overflow-x-auto relative">
              {loadingRows && (
                <div className="absolute inset-0 bg-white/70 z-10 flex items-center justify-center">
                  <Loader2 className="w-6 h-6 animate-spin text-amber-500" />
                </div>
              )}
              <table className="w-full text-xs">
                <thead className="bg-slate-50 text-slate-500 text-left">
                  <tr>
                    {table.columns.map((c) => (
                      <th key={c.name} className="px-4 py-2.5 font-semibold whitespace-nowrap">
                        {c.label}
                      </th>
                    ))}
                    <th className="px-4 py-2.5 font-semibold whitespace-nowrap">En uso</th>
                    <th className="px-4 py-2.5" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/70">
                      {table.columns.map((c) => (
                        <td key={c.name} className={`px-4 py-2.5 align-top ${c.name === 'code' || c.name === 'key' ? 'font-mono text-slate-700' : 'text-slate-800'} max-w-xs`}>
                          <span className="line-clamp-2">{cellText(c, r[c.name])}</span>
                        </td>
                      ))}
                      <td className="px-4 py-2.5 text-slate-500">{r.usage_count ? `${r.usage_count} registro(s)` : '—'}</td>
                      <td className="px-4 py-2.5 text-right whitespace-nowrap">
                        <button
                          onClick={() => setModal({ row: r })}
                          className="p-1.5 text-slate-500 hover:text-amber-700 hover:bg-amber-50 rounded-lg"
                          title="Editar"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        {table.can_delete && (
                          <button
                            onClick={() => remove(r)}
                            disabled={!!busyId || r.usage_count > 0}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg disabled:opacity-30 disabled:hover:bg-transparent"
                            title={r.usage_count > 0 ? 'En uso: no se puede eliminar' : 'Eliminar'}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {!loadingRows && filtered.length === 0 && (
                    <tr>
                      <td colSpan={table.columns.length + 2} className="px-4 py-10 text-center text-slate-400">
                        Sin registros.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-2 border-t border-slate-100 text-[11px] text-slate-400">
              {filtered.length} de {rows.length} registro(s)
            </div>
          </section>
        </div>
      )}

      {modal && table && <RowModal table={table} row={modal.row} onClose={() => setModal(null)} onSaved={afterChange} />}
    </div>
  );
};
