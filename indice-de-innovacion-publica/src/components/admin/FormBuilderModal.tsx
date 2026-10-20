import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { IIPForm, FormSection, FormQuestion, FormField, QuestionKind, FileTypeInfo } from '../../types';
import { coreService } from '../../services/coreService';
import {
  X,
  Loader2,
  Plus,
  Trash2,
  AlertCircle,
  ChevronUp,
  ChevronDown,
  FileText,
  Check,
  CornerDownRight,
  Repeat,
} from 'lucide-react';
import { FORM_ICONS, FormIcon } from '../common/formIcons';
import {
  DEFAULT_MAX_FILE_SIZE,
  LOOP_FIELD_KINDS,
  QUESTION_KINDS,
  getIndicators,
  isChoiceType,
  kindOf,
  newChoice,
  newField,
  newIndicator,
  newQuestion,
  newVariable,
  normalizeCodes,
  numberQuestions,
  questionFields,
  findFormIssue,
} from '../../utils/formTree';

interface FormBuilderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (form: IIPForm) => Promise<IIPForm>;
  initialForm?: IIPForm | null;
}

const FileTypesCtx = createContext<FileTypeInfo[]>([]);

const MB = 1024 * 1024;
const formatSize = (bytes: number) => (bytes >= MB ? `${+(bytes / MB).toFixed(1)} MB` : `${Math.round(bytes / 1024)} KB`);
const formatDate = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleString('es-CO', { dateStyle: 'long', timeStyle: 'short' }) : null;

type Selection = { v: number; i: number | null };

const inputCls =
  'w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-hidden focus:border-amber-500 focus:ring-1 focus:ring-amber-500';
const labelCls = 'block text-[11px] font-semibold text-slate-600 mb-1';

const emptyDraft = () => ({
  label: '',
  code: `IIP_${new Date().getFullYear()}_V1`,
  description: '',
  year: new Date().getFullYear(),
  version: '1.0',
  isActive: true,
  sections: [newVariable(1)] as FormSection[],
});

/* ------------------------------------------------------------------ */
/* Pequeños componentes de edición                                     */
/* ------------------------------------------------------------------ */

const IconPicker: React.FC<{ value?: string; onChange: (v: string) => void }> = ({ value, onChange }) => (
  <div className="flex flex-wrap gap-1.5">
    {Object.entries(FORM_ICONS).map(([name, { label, Icon }]) => (
      <button
        key={name}
        type="button"
        title={label}
        onClick={() => onChange(name)}
        className={`w-8 h-8 rounded-lg border flex items-center justify-center transition-colors ${
          value === name
            ? 'bg-slate-900 border-slate-900 text-amber-400'
            : 'bg-white border-slate-200 text-slate-500 hover:border-slate-400'
        }`}
      >
        <Icon className="w-4 h-4" />
      </button>
    ))}
  </div>
);

/** Nombre, descripción, ayuda e ícono: lo que comparten Variables e Indicadores. */
const SectionMeta: React.FC<{
  kindLabel: string;
  section: FormSection;
  onChange: (updates: Partial<FormSection>) => void;
}> = ({ kindLabel, section, onChange }) => (
  <div className="space-y-3">
    <div>
      <label className={labelCls}>Nombre de la {kindLabel.toLowerCase()} *</label>
      <input
        className={inputCls}
        value={section.label}
        maxLength={255}
        onChange={(e) => onChange({ label: e.target.value })}
        placeholder={kindLabel === 'Variable' ? 'Ej. Capacidades institucionales' : 'Ej. Marco normativo de innovación'}
      />
    </div>
    <div>
      <label className={labelCls}>Descripción</label>
      <textarea
        className={`${inputCls} min-h-[60px]`}
        value={section.description ?? ''}
        onChange={(e) => onChange({ description: e.target.value })}
      />
    </div>
    <div>
      <label className={labelCls}>Texto de ayuda</label>
      <textarea
        className={`${inputCls} min-h-[48px]`}
        value={section.help_text ?? ''}
        onChange={(e) => onChange({ help_text: e.target.value })}
        placeholder="Orientación que verá quien diligencie el formulario"
      />
    </div>
    <div>
      <label className={labelCls}>Ícono</label>
      <IconPicker value={section.icon_name} onChange={(icon_name) => onChange({ icon_name })} />
    </div>
  </div>
);

const ChoicesEditor: React.FC<{
  field: FormField;
  onChange: (updates: Partial<FormField>) => void;
}> = ({ field, onChange }) => {
  const choices = field.choices ?? [];
  return (
    <div className="space-y-1.5">
      <div className="text-[11px] font-semibold text-slate-600">
        Opciones ({field.field_type_code === 'multichoice' ? 'se puede marcar más de una' : 'se elige una'})
      </div>
      {choices.map((c, idx) => (
        <div key={c.id} className="flex items-center gap-1.5">
          <span className="text-[10px] text-slate-400 w-4 text-right">{idx + 1}.</span>
          <input
            className={inputCls}
            value={c.label}
            placeholder={`Opción ${idx + 1}`}
            onChange={(e) =>
              onChange({ choices: choices.map((x) => (x.id === c.id ? { ...x, label: e.target.value } : x)) })
            }
          />
          <button
            type="button"
            disabled={choices.length <= 2}
            onClick={() => onChange({ choices: choices.filter((x) => x.id !== c.id) })}
            className="p-1.5 text-slate-400 hover:text-rose-600 disabled:opacity-30"
            title="Quitar opción"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={() => onChange({ choices: [...choices, newChoice(choices.length + 1)] })}
        className="text-[11px] font-semibold text-amber-700 hover:text-amber-900 flex items-center gap-1"
      >
        <Plus className="w-3 h-3" /> Agregar opción
      </button>
    </div>
  );
};

/** Campo `file`: tipos de archivo permitidos y tamaño máximo. */
const FileExtras: React.FC<{
  field: FormField;
  onChange: (updates: Partial<FormField>) => void;
}> = ({ field, onChange }) => {
  const fileTypes = useContext(FileTypesCtx);
  const selected = field.allowed_file_types ?? [];
  const limit = selected.length
    ? Math.min(...fileTypes.filter((t) => selected.includes(t.code)).map((t) => t.max_size))
    : null;
  const categories = [...new Set(fileTypes.map((t) => t.category))];

  const toggle = (code: string) => {
    const next = selected.includes(code) ? selected.filter((c) => c !== code) : [...selected, code];
    const nextLimit = next.length
      ? Math.min(...fileTypes.filter((t) => next.includes(t.code)).map((t) => t.max_size))
      : null;
    onChange({
      allowed_file_types: next,
      max_file_size: nextLimit && (field.max_file_size ?? 0) > nextLimit ? nextLimit : field.max_file_size,
    });
  };

  return (
    <div className="space-y-2">
      <div className="text-[11px] font-semibold text-slate-600">Tipos de archivo permitidos *</div>
      {fileTypes.length === 0 && <p className="text-[11px] text-slate-500">Cargando tipos de archivo…</p>}
      {categories.map((cat) => (
        <div key={cat} className="flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 w-20 shrink-0">{cat}</span>
          {fileTypes
            .filter((t) => t.category === cat)
            .map((t) => (
              <label
                key={t.code}
                title={`${t.mime_type} · máx. ${formatSize(t.max_size)}`}
                className={`px-2 py-1 rounded-lg border text-[11px] cursor-pointer select-none ${
                  selected.includes(t.code)
                    ? 'bg-slate-900 border-slate-900 text-amber-300'
                    : 'bg-white border-slate-200 text-slate-600 hover:border-slate-400'
                }`}
              >
                <input type="checkbox" className="hidden" checked={selected.includes(t.code)} onChange={() => toggle(t.code)} />
                {t.extension}
              </label>
            ))}
        </div>
      ))}
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className={labelCls}>Tamaño máximo (MB) *</label>
          <input
            type="number"
            min={0.1}
            step={0.5}
            className={`${inputCls} !w-32`}
            value={field.max_file_size ? +(field.max_file_size / MB).toFixed(2) : ''}
            onChange={(e) => {
              const bytes = Math.round(Number(e.target.value) * MB);
              onChange({ max_file_size: limit ? Math.min(bytes, limit) : bytes });
            }}
          />
        </div>
        <p className="text-[11px] text-slate-500 pb-2">
          {limit ? `Límite de los tipos elegidos: ${formatSize(limit)}.` : 'Elija al menos un tipo para ver el límite.'}
        </p>
      </div>
    </div>
  );
};

/** Opciones, unidad y rango propios del tipo de campo. */
const FieldTypeExtras: React.FC<{
  field: FormField;
  onChange: (updates: Partial<FormField>) => void;
}> = ({ field, onChange }) => {
  if (field.field_type_code === 'file') return <FileExtras field={field} onChange={onChange} />;
  if (isChoiceType(field.field_type_code)) return <ChoicesEditor field={field} onChange={onChange} />;
  if (field.field_type_code === 'numeric')
    return (
      <div className="grid grid-cols-3 gap-2">
        <div>
          <label className={labelCls}>Unidad</label>
          <input
            className={inputCls}
            value={field.unit ?? ''}
            onChange={(e) => onChange({ unit: e.target.value || undefined })}
            placeholder="Ej. personas"
          />
        </div>
        <div>
          <label className={labelCls}>Mínimo</label>
          <input
            type="number"
            className={inputCls}
            value={field.min_value ?? ''}
            onChange={(e) => onChange({ min_value: e.target.value === '' ? undefined : Number(e.target.value) })}
          />
        </div>
        <div>
          <label className={labelCls}>Máximo</label>
          <input
            type="number"
            className={inputCls}
            value={field.max_value ?? ''}
            onChange={(e) => onChange({ max_value: e.target.value === '' ? undefined : Number(e.target.value) })}
          />
        </div>
      </div>
    );
  return null;
};

/* ------------------------------------------------------------------ */
/* Editor de una pregunta                                              */
/* ------------------------------------------------------------------ */

const QuestionEditor: React.FC<{
  highlighted?: boolean;
  question: FormQuestion;
  number: string;
  siblings: FormQuestion[];
  index: number;
  total: number;
  onChange: (q: FormQuestion) => void;
  onMove: (dir: 'up' | 'down') => void;
  onRemove: () => void;
}> = ({ highlighted, question, number, siblings, index, total, onChange, onMove, onRemove }) => {
  const kind = kindOf(question);
  const fields = questionFields(question);
  const isLoop = kind === 'loop';

  // Preguntas Sí/No anteriores: candidatas a "padre" de un bucle.
  const parents = siblings.slice(0, index).filter((p) => kindOf(p) === 'boolean');

  const setFields = (next: FormField[]) =>
    onChange({
      ...question,
      card_template: {
        ...question.card_template,
        field_groups: [{ ...question.card_template.field_groups[0], fields: next }],
      },
    });

  const updateField = (fid: string, updates: Partial<FormField>) =>
    setFields(fields.map((f) => (f.id === fid ? { ...f, ...updates } : f)));

  const changeKind = (next: QuestionKind) => {
    if (next === kind) return;
    const fresh = newQuestion(next, index + 1);
    onChange({
      ...fresh,
      id: question.id,
      code: question.code,
      label: question.label,
      help_text: question.help_text,
      is_required: question.is_required,
      depends_on: next === 'loop' ? (question.depends_on ?? (parents.length ? { question_id: parents[parents.length - 1].id, value: true } : null)) : null,
    });
  };

  // Para una pregunta simple, el enunciado es también el texto del campo.
  const setLabel = (label: string) => {
    if (isLoop) return onChange({ ...question, label });
    onChange({
      ...question,
      label,
      card_template: {
        ...question.card_template,
        field_groups: [
          {
            ...question.card_template.field_groups[0],
            fields: fields.map((f, i) => (i === 0 ? { ...f, label } : f)),
          },
        ],
      },
    });
  };

  return (
    <div id={`q-${question.id}`} className={`rounded-2xl border p-4 space-y-3 ${highlighted ? 'ring-2 ring-rose-500 ' : ''}${isLoop ? 'bg-amber-50/40 border-amber-200 ml-4 sm:ml-8' : 'bg-white border-slate-200'}`}>
      <div className="flex items-start gap-3">
        <div
          className={`min-w-9 h-9 px-2 rounded-xl flex items-center justify-center text-xs font-black shrink-0 ${
            isLoop ? 'bg-amber-500 text-slate-950' : 'bg-slate-900 text-amber-400'
          }`}
        >
          {number}
        </div>
        <div className="flex-1 min-w-0 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
            <div>
              <label className={labelCls}>Enunciado de la pregunta *</label>
              <textarea
                className={`${inputCls} min-h-[56px]`}
                value={question.label}
                maxLength={255}
                onChange={(e) => setLabel(e.target.value)}
                placeholder={
                  isLoop
                    ? 'Ej. ¿Qué actos administrativos existen o existieron? Ingrese cada uno y sus detalles'
                    : 'Escriba la pregunta tal como la verá la entidad'
                }
              />
            </div>
            <div className="sm:w-52">
              <label className={labelCls}>Tipo de pregunta</label>
              <select className={inputCls} value={kind} onChange={(e) => changeKind(e.target.value as QuestionKind)}>
                {QUESTION_KINDS.map((k) => (
                  <option key={k.value} value={k.value}>
                    {k.label}
                  </option>
                ))}
              </select>
              <label className="mt-2 flex items-center gap-2 text-[11px] text-slate-600">
                <input
                  type="checkbox"
                  checked={question.is_required ?? true}
                  onChange={(e) => onChange({ ...question, is_required: e.target.checked })}
                />
                Obligatoria
              </label>
            </div>
          </div>

          <div>
            <label className={labelCls}>Texto de ayuda</label>
            <input
              className={inputCls}
              value={question.help_text ?? ''}
              onChange={(e) => onChange({ ...question, help_text: e.target.value })}
              placeholder="Opcional"
            />
          </div>

          {!isLoop && <FieldTypeExtras field={fields[0]} onChange={(u) => updateField(fields[0].id, u)} />}

          {isLoop && (
            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-white border border-amber-200 space-y-2">
                <div className="flex items-center gap-1.5 text-[11px] font-bold text-amber-800">
                  <CornerDownRight className="w-3.5 h-3.5" /> Condición para responder este bucle
                </div>
                {parents.length === 0 ? (
                  <p className="text-[11px] text-slate-600">
                    Sin condición: este bucle siempre se responde. Para habilitarlo según una respuesta, agregue antes
                    una pregunta Sí/No en este indicador.
                  </p>
                ) : (
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-700">
                    <span>Responder solo si la pregunta</span>
                    <select
                      className={`${inputCls} !w-auto`}
                      value={question.depends_on?.question_id ?? ''}
                      onChange={(e) =>
                        onChange({
                          ...question,
                          depends_on: e.target.value
                            ? { question_id: e.target.value, value: question.depends_on?.value ?? true }
                            : null,
                        })
                      }
                    >
                      <option value="">— ninguna (siempre se responde) —</option>
                      {parents.map((p) => (
                        <option key={p.id} value={p.id}>
                          {`${p.label.slice(0, 50) || 'Sin enunciado'}`}
                        </option>
                      ))}
                    </select>
                    <span>es</span>
                    <select
                      className={`${inputCls} !w-auto`}
                      disabled={!question.depends_on}
                      value={question.depends_on?.value === false ? 'no' : 'si'}
                      onChange={(e) =>
                        question.depends_on &&
                        onChange({ ...question, depends_on: { ...question.depends_on, value: e.target.value === 'si' } })
                      }
                    >
                      <option value="si">Sí</option>
                      <option value="no">No</option>
                    </select>
                    <span>{question.depends_on ? '; en caso contrario pasa a la siguiente pregunta.' : ''}</span>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-700">
                  <Repeat className="w-3.5 h-3.5" /> Campos de cada tarjeta (se repite por cada registro)
                </div>
                {fields.map((f, fi) => (
                  <div key={f.id} className="p-3 rounded-xl bg-white border border-slate-200 space-y-2">
                    <div className="grid grid-cols-1 sm:grid-cols-[1fr_11rem_auto] gap-2 items-end">
                      <div>
                        <label className={labelCls}>Campo {fi + 1} *</label>
                        <input
                          className={inputCls}
                          value={f.label}
                          onChange={(e) => updateField(f.id, { label: e.target.value })}
                          placeholder="Ej. Número del acto administrativo"
                        />
                      </div>
                      <div>
                        <label className={labelCls}>Tipo</label>
                        <select
                          className={inputCls}
                          value={f.field_type_code}
                          onChange={(e) => {
                            const t = e.target.value as FormField['field_type_code'];
                            updateField(f.id, {
                              field_type_code: t,
                              field_type_id: `ft-${t}`,
                              choices: isChoiceType(t) ? (f.choices?.length ? f.choices : [newChoice(1), newChoice(2)]) : undefined,
                              allowed_file_types: t === 'file' ? (f.allowed_file_types ?? []) : undefined,
                              max_file_size: t === 'file' ? (f.max_file_size ?? DEFAULT_MAX_FILE_SIZE) : undefined,
                            });
                          }}
                        >
                          {LOOP_FIELD_KINDS.map((k) => (
                            <option key={k.value} value={k.value}>
                              {k.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="flex items-center gap-2 pb-1.5">
                        <label className="flex items-center gap-1.5 text-[11px] text-slate-600">
                          <input
                            type="checkbox"
                            checked={f.is_required}
                            onChange={(e) => updateField(f.id, { is_required: e.target.checked })}
                          />
                          Obligatorio
                        </label>
                        <button
                          type="button"
                          disabled={fields.length <= 1}
                          onClick={() => setFields(fields.filter((x) => x.id !== f.id))}
                          className="p-1.5 text-slate-400 hover:text-rose-600 disabled:opacity-30"
                          title="Quitar campo"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div>
                      <label className={labelCls}>Texto de ayuda del campo</label>
                      <input
                        className={inputCls}
                        value={f.help_text ?? ''}
                        onChange={(e) => updateField(f.id, { help_text: e.target.value })}
                        placeholder="Orientación para diligenciar este campo (opcional)"
                      />
                    </div>
                    <FieldTypeExtras field={f} onChange={(u) => updateField(f.id, u)} />
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => setFields([...fields, newField(fields.length + 1, 'text')])}
                  className="text-[11px] font-semibold text-amber-700 hover:text-amber-900 flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" /> Agregar campo a la tarjeta
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-0.5 shrink-0">
          <button
            type="button"
            disabled={index === 0}
            onClick={() => onMove('up')}
            className="p-1 text-slate-400 hover:text-slate-900 disabled:opacity-30"
            title="Subir"
          >
            <ChevronUp className="w-4 h-4" />
          </button>
          <button
            type="button"
            disabled={index === total - 1}
            onClick={() => onMove('down')}
            className="p-1 text-slate-400 hover:text-slate-900 disabled:opacity-30"
            title="Bajar"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={onRemove}
            className="p-1 text-slate-400 hover:text-rose-600"
            title="Eliminar pregunta"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Modal principal                                                     */
/* ------------------------------------------------------------------ */

export const FormBuilderModal: React.FC<FormBuilderModalProps> = ({ isOpen, onClose, onSave, initialForm }) => {
  const [draft, setDraft] = useState(emptyDraft);
  const [sel, setSel] = useState<Selection>({ v: 0, i: 0 });
  const [isSaving, setIsSaving] = useState(false);
  const [savePhase, setSavePhase] = useState<'saving' | 'reloading'>('saving');
  // Evita dobles guardados (doble clic o seguir editando mientras el PUT se refleja).
  const savingRef = useRef(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [highlightId, setHighlightId] = useState<string | null>(null);
  const [fileTypes, setFileTypes] = useState<FileTypeInfo[]>([]);
  // Formulario tal como quedó guardado por última vez (permite seguir editando tras guardar).
  const [base, setBase] = useState<IIPForm | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    coreService.getFileTypes().then(setFileTypes).catch(() => setFileTypes([]));
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    setBase(initialForm ?? null);
    if (initialForm) {
      setDraft({
        label: initialForm.label,
        code: initialForm.code,
        description: initialForm.description ?? '',
        year: initialForm.year,
        version: initialForm.version,
        isActive: initialForm.is_active,
        sections: structuredClone(initialForm.sections),
      });
    } else {
      setDraft(emptyDraft());
    }
    setSel({ v: 0, i: initialForm ? (getIndicators(initialForm.sections[0] ?? ({} as FormSection)).length ? 0 : null) : 0 });
    setErrorMsg(null);
  }, [isOpen, initialForm]);

  const sections = draft.sections;
  const safeV = Math.min(sel.v, Math.max(0, sections.length - 1));
  const variable = sections[safeV];
  const indicators = variable ? getIndicators(variable) : [];
  const safeI = sel.i === null ? null : Math.min(sel.i, Math.max(0, indicators.length - 1));
  const indicator = safeI !== null ? indicators[safeI] : undefined;
  const questions = indicator?.questions ?? [];
  const numbering = useMemo(() => numberQuestions(questions), [questions]);

  if (!isOpen) return null;

  const mutate = (fn: (secs: FormSection[]) => void) =>
    setDraft((d) => {
      const copy = structuredClone(d.sections);
      fn(copy);
      return { ...d, sections: copy };
    });

  const move = <T,>(arr: T[], idx: number, dir: 'up' | 'down') => {
    const t = dir === 'up' ? idx - 1 : idx + 1;
    if (t < 0 || t >= arr.length) return false;
    [arr[idx], arr[t]] = [arr[t], arr[idx]];
    return true;
  };

  const moveVariable = (v: number, dir: 'up' | 'down') => {
    mutate((s) => void move(s, v, dir));
    setSel({ v: dir === 'up' ? v - 1 : v + 1, i: null });
  };
  const addVariable = () => {
    mutate((s) => s.push(newVariable(s.length + 1)));
    setSel({ v: sections.length, i: 0 });
  };
  const removeVariable = (v: number) => {
    if (sections.length <= 1) return alert('El formulario necesita al menos una variable.');
    if (!confirm('¿Eliminar la variable con todos sus indicadores y preguntas?')) return;
    mutate((s) => s.splice(v, 1));
    setSel({ v: Math.max(0, v - 1), i: 0 });
  };
  const addIndicator = (v: number) => {
    const n = getIndicators(sections[v]).length + 1;
    mutate((s) => {
      s[v].children = [...getIndicators(s[v]), newIndicator(s[v].code, n)];
    });
    setSel({ v, i: n - 1 });
  };
  const removeIndicator = (v: number, i: number) => {
    if (getIndicators(sections[v]).length <= 1) return alert('La variable necesita al menos un indicador.');
    if (!confirm('¿Eliminar el indicador con todas sus preguntas?')) return;
    mutate((s) => s[v].children!.splice(i, 1));
    setSel({ v, i: Math.max(0, i - 1) });
  };

  const patchVariable = (updates: Partial<FormSection>) => mutate((s) => Object.assign(s[safeV], updates));
  const patchIndicator = (updates: Partial<FormSection>) =>
    safeI !== null && mutate((s) => Object.assign(s[safeV].children![safeI], updates));
  const patchQuestions = (fn: (qs: FormQuestion[]) => void) =>
    safeI !== null && mutate((s) => fn((s[safeV].children![safeI].questions ??= [])));

  const addQuestion = (kind: QuestionKind) => {
    const q = newQuestion(kind, questions.length + 1);
    if (kind === 'loop') {
      const lastBool = [...questions].reverse().find((p) => kindOf(p) === 'boolean');
      q.depends_on = lastBool ? { question_id: lastBool.id, value: true } : null;
    }
    patchQuestions((qs) => qs.push(q));
  };

  const handleSave = async () => {
    if (savingRef.current) return;
    if (!draft.label.trim()) return setErrorMsg('El nombre del formulario es obligatorio.');
    if (!draft.code.trim()) return setErrorMsg('El código del formulario es obligatorio.');

    const compiled = normalizeCodes({
      id: base?.id || `form-iip-${Date.now()}`,
      code: draft.code.trim().toUpperCase(),
      label: draft.label.trim(),
      description: draft.description.trim() || null,
      year: Number(draft.year),
      version: draft.version.trim() || '1.0',
      is_active: draft.isActive,
      sections: draft.sections,
      is_synced_to_backend: base?.is_synced_to_backend ?? false,
      updated_at: base?.updated_at ?? null,
    });

    const issue = findFormIssue(compiled);
    if (issue) {
      // Llevar al admin al lugar exacto del problema; un texto pequeño abajo pasa desapercibido.
      setSel({ v: issue.v, i: issue.i });
      setHighlightId(issue.questionId ?? null);
      setErrorMsg(issue.message);
      requestAnimationFrame(() =>
        document.getElementById(`q-${issue.questionId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      );
      alert(`No se pudo guardar:\n${issue.message}`);
      return;
    }
    setHighlightId(null);

    savingRef.current = true;
    setSavePhase('saving');
    setIsSaving(true);
    setErrorMsg(null);
    try {
      await onSave(compiled);
      // El editor queda bloqueado (loader) hasta recargar la pantalla con lo ya guardado.
      setSavePhase('reloading');
      await new Promise((r) => setTimeout(r, 60)); // dejar pintar el loader antes de la alerta
      alert('Formulario guardado correctamente.');
      window.location.reload();
    } catch (err: any) {
      const message = err?.message || 'Error al guardar el formulario.';
      setErrorMsg(message);
      savingRef.current = false;
      setIsSaving(false);
      alert(`No se pudo guardar:\n${message}`);
    }
  };

  return (
    <FileTypesCtx.Provider value={fileTypes}>
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-3 sm:p-6">
      <div className="relative bg-white w-full max-w-6xl rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh]">
        {isSaving && (
          <div className="absolute inset-0 z-20 bg-white/85 backdrop-blur-[2px] flex flex-col items-center justify-center gap-3 cursor-wait">
            <Loader2 className="w-10 h-10 text-amber-500 animate-spin" />
            <p className="text-sm font-bold text-slate-800">
              {savePhase === 'saving' ? 'Guardando el formulario…' : 'Guardado. Actualizando la pantalla…'}
            </p>
            <p className="text-xs text-slate-500">No cierre ni edite hasta que termine.</p>
          </div>
        )}
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500 text-slate-950 flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-base leading-tight">
                {base ? 'Editar formulario' : 'Nuevo formulario'}
              </h2>
              <p className="text-[11px] text-slate-400">Variables → Indicadores → Preguntas</p>
            </div>
          </div>
          <button disabled={isSaving} onClick={onClose} className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Datos generales */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 grid grid-cols-1 md:grid-cols-6 gap-3">
          <div className="md:col-span-3">
            <label className={labelCls}>Nombre del formulario *</label>
            <input className={inputCls} value={draft.label} maxLength={255} onChange={(e) => setDraft({ ...draft, label: e.target.value })} />
          </div>
          <div>
            <label className={labelCls}>Código *</label>
            <input
              className={`${inputCls} font-mono`}
              value={draft.code}
              maxLength={50}
              disabled={!!base?.is_synced_to_backend}
              onChange={(e) => setDraft({ ...draft, code: e.target.value.toUpperCase() })}
            />
          </div>
          <div>
            <label className={labelCls}>Año</label>
            <input type="number" className={inputCls} value={draft.year} onChange={(e) => setDraft({ ...draft, year: Number(e.target.value) })} />
          </div>
          <div>
            <label className={labelCls}>Versión</label>
            <input className={inputCls} value={draft.version} onChange={(e) => setDraft({ ...draft, version: e.target.value })} />
          </div>
          <div className="md:col-span-6">
            <label className={labelCls}>Descripción</label>
            <input className={inputCls} value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })} />
          </div>
        </div>

        {/* Árbol + editor */}
        <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-[18rem_1fr]">
          {/* Árbol */}
          <div className="border-b md:border-b-0 md:border-r border-slate-200 bg-slate-50/60 overflow-y-auto p-3 space-y-2 max-h-64 md:max-h-none">
            {sections.map((v, vi) => {
              const inds = getIndicators(v);
              const vSelected = safeV === vi && safeI === null;
              return (
                <div key={v.id} className="rounded-xl border border-slate-200 bg-white overflow-hidden">
                  <div className={`flex items-center gap-1 pr-1 ${vSelected ? 'bg-slate-900 text-white' : ''}`}>
                    <button
                      type="button"
                      onClick={() => setSel({ v: vi, i: null })}
                      className="flex-1 min-w-0 flex items-center gap-2 px-3 py-2 text-left"
                    >
                      <FormIcon name={v.icon_name} className={`w-4 h-4 shrink-0 ${vSelected ? 'text-amber-400' : 'text-amber-600'}`} />
                      <span className="text-xs font-bold truncate">
                        {vi + 1}. {v.label || 'Variable sin nombre'}
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => moveVariable(vi, 'up')}
                      disabled={vi === 0}
                      className="p-1 opacity-60 hover:opacity-100 disabled:opacity-20"
                    >
                      <ChevronUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => moveVariable(vi, 'down')}
                      disabled={vi === sections.length - 1}
                      className="p-1 opacity-60 hover:opacity-100 disabled:opacity-20"
                    >
                      <ChevronDown className="w-3.5 h-3.5" />
                    </button>
                    <button type="button" onClick={() => removeVariable(vi)} className="p-1 opacity-60 hover:text-rose-500 hover:opacity-100">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="border-t border-slate-100 py-1">
                    {inds.map((ind, ii) => {
                      const iSelected = safeV === vi && safeI === ii;
                      return (
                        <div key={ind.id} className={`flex items-center pr-1 ${iSelected ? 'bg-amber-50' : ''}`}>
                          <button
                            type="button"
                            onClick={() => setSel({ v: vi, i: ii })}
                            className="flex-1 min-w-0 flex items-center gap-2 pl-6 pr-2 py-1.5 text-left"
                          >
                            <FormIcon name={ind.icon_name} className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                            <span className={`text-[11px] truncate ${iSelected ? 'font-bold text-slate-900' : 'text-slate-600'}`}>
                              {vi + 1}.{ii + 1} {ind.label || 'Indicador sin nombre'}
                            </span>
                          </button>
                          <button
                            type="button"
                            onClick={() => removeIndicator(vi, ii)}
                            className="p-1 text-slate-300 hover:text-rose-500"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      );
                    })}
                    <button
                      type="button"
                      onClick={() => addIndicator(vi)}
                      className="w-full pl-6 pr-2 py-1.5 text-left text-[11px] font-semibold text-amber-700 hover:bg-amber-50 flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> Agregar indicador
                    </button>
                  </div>
                </div>
              );
            })}
            <button
              type="button"
              onClick={addVariable}
              className="w-full px-3 py-2 rounded-xl border border-dashed border-slate-300 text-xs font-bold text-slate-600 hover:border-amber-500 hover:text-amber-700 flex items-center justify-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" /> Agregar variable
            </button>
          </div>

          {/* Editor */}
          <div className="overflow-y-auto p-5 space-y-5">
            {errorMsg && (
              <div className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}
            {variable && safeI === null && (
              <>
                <h3 className="text-sm font-bold text-slate-900">Variable {safeV + 1}</h3>
                <SectionMeta kindLabel="Variable" section={variable} onChange={patchVariable} />
                <p className="text-[11px] text-slate-500">
                  Esta variable tiene {indicators.length} indicador(es). Selecciónelos en el árbol para editar sus preguntas.
                </p>
              </>
            )}

            {variable && indicator && (
              <>
                <div className="text-[11px] text-slate-500">
                  Variable {safeV + 1}: <strong className="text-slate-700">{variable.label || 'sin nombre'}</strong>
                </div>
                <h3 className="text-sm font-bold text-slate-900">
                  Indicador {safeV + 1}.{(safeI ?? 0) + 1}
                </h3>
                <SectionMeta kindLabel="Indicador" section={indicator} onChange={patchIndicator} />

                <div className="pt-2 border-t border-slate-200 space-y-3">
                  <h4 className="text-xs font-bold text-slate-900">Preguntas del indicador ({questions.length})</h4>
                  {questions.map((q, qi) => (
                    <QuestionEditor
                      key={q.id}
                      highlighted={highlightId === q.id}
                      question={q}
                      number={numbering[q.id]}
                      siblings={questions}
                      index={qi}
                      total={questions.length}
                      onChange={(next) => patchQuestions((qs) => void (qs[qi] = next))}
                      onMove={(dir) => patchQuestions((qs) => void move(qs, qi, dir))}
                      onRemove={() => {
                        if (questions.length <= 1) return alert('El indicador necesita al menos una pregunta.');
                        patchQuestions((qs) => {
                          qs.splice(qi, 1);
                          // Un bucle sin su pregunta padre queda sin condición.
                          qs.forEach((x) => {
                            if (x.depends_on?.question_id === q.id) x.depends_on = null;
                          });
                        });
                      }}
                    />
                  ))}

                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <span className="text-[11px] font-semibold text-slate-500">Agregar pregunta:</span>
                    {QUESTION_KINDS.map((k) => (
                      <button
                        key={k.value}
                        type="button"
                        onClick={() => addQuestion(k.value)}
                        className={`px-2.5 py-1.5 rounded-lg text-[11px] font-semibold border transition-colors ${
                          k.value === 'loop'
                            ? 'border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100'
                            : 'border-slate-200 bg-white text-slate-700 hover:border-slate-400'
                        }`}
                      >
                        + {k.label}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="min-h-[1.25rem] space-y-1">
            <div className="text-[11px] text-slate-500">
              {formatDate(base?.updated_at)
                ? `Última actualización: ${formatDate(base?.updated_at)}`
                : 'Última actualización: aún no se ha guardado en el servidor'}
            </div>
            {errorMsg && (
              <div className="flex items-start gap-1.5 text-xs text-rose-700">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 justify-end">
            <button disabled={isSaving} onClick={onClose} className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl">
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-5 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-extrabold rounded-xl flex items-center gap-1.5 disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              {isSaving ? 'Guardando…' : 'Guardar formulario'}
            </button>
          </div>
        </div>
      </div>
    </div>
    </FileTypesCtx.Provider>
  );
};
