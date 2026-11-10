import React from 'react';
import { AlertCircle } from 'lucide-react';
import { FormField } from '../../../types';

interface FieldInputProps {
  field: FormField;
  value: any;
  onChange: (value: any) => void;
  error?: string;
  /** Id único del campo en el DOM (un mismo campo se repite en cada ficha). */
  domId: string;
  /** Oculta la etiqueta cuando la pregunta ya la muestra como enunciado. */
  hideLabel?: boolean;
}

const inputBase =
  'iip-focus w-full rounded-xl border bg-white px-3.5 py-2.5 text-[15px] text-iip-ink placeholder:text-slate-400';

const optionBase =
  'flex cursor-pointer items-center gap-3 rounded-xl border bg-white px-4 py-3 text-[15px] text-iip-ink transition-colors ' +
  'border-iip-line hover:border-iip-navy-700/50 has-[input:checked]:border-iip-navy-700 has-[input:checked]:bg-iip-sky ' +
  'has-[input:focus-visible]:outline-3 has-[input:focus-visible]:outline-offset-2 has-[input:focus-visible]:outline-iip-navy-700';

/** Opción de radio/checkbox con el input nativo (teclado y lector de pantalla) y un indicador visual propio. */
const Option: React.FC<{
  type: 'radio' | 'checkbox';
  name: string;
  checked: boolean;
  label: string;
  onChange: () => void;
}> = ({ type, name, checked, label, onChange }) => (
  <label className={optionBase}>
    <input type={type} name={name} checked={checked} onChange={onChange} className="peer sr-only" />
    <span
      aria-hidden="true"
      className={`flex h-5 w-5 shrink-0 items-center justify-center border-2 ${type === 'radio' ? 'rounded-full' : 'rounded-md'} ${
        checked ? 'border-iip-navy-700 bg-iip-navy-700' : 'border-slate-400 bg-white'
      }`}
    >
      {checked && <span className={`bg-white ${type === 'radio' ? 'h-2 w-2 rounded-full' : 'h-2.5 w-2.5 rounded-[2px]'}`} />}
    </span>
    <span>{label}</span>
  </label>
);

export const FieldInput: React.FC<FieldInputProps> = ({ field, value, onChange, error, domId, hideLabel }) => {
  const errId = `${domId}-err`;
  const hasError = !!error;
  const a11y = {
    'aria-required': field.is_required || undefined,
    'aria-invalid': hasError || undefined,
    'aria-describedby': hasError ? errId : undefined,
  };
  const borderCls = hasError ? 'border-rose-400 bg-rose-50/50' : 'border-iip-line';
  const type = field.field_type_code;

  const label = !hideLabel && field.label && (
    <span className="mb-1.5 block text-sm font-bold text-iip-ink">
      {field.label}
      {field.is_required && <span className="ml-1 text-rose-600" aria-hidden="true">*</span>}
    </span>
  );

  let control: React.ReactNode = null;

  if (type === 'boolean') {
    control = (
      <div role="radiogroup" aria-label={field.label} className="space-y-2" {...a11y}>
        <Option type="radio" name={domId} checked={value === true} label="Sí" onChange={() => onChange(true)} />
        <Option type="radio" name={domId} checked={value === false} label="No" onChange={() => onChange(false)} />
      </div>
    );
  } else if (type === 'singlechoice') {
    control = (
      <div role="radiogroup" aria-label={field.label} className="space-y-2" {...a11y}>
        {(field.choices ?? []).map((c) => (
          <Option key={c.id} type="radio" name={domId} checked={value === c.id || value === c.code} label={c.label} onChange={() => onChange(c.id)} />
        ))}
      </div>
    );
  } else if (type === 'multichoice') {
    const selected: string[] = Array.isArray(value) ? value : [];
    control = (
      <div role="group" aria-label={field.label} className="space-y-2" {...a11y}>
        {(field.choices ?? []).map((c) => {
          const on = selected.includes(c.id);
          return (
            <Option
              key={c.id}
              type="checkbox"
              name={`${domId}-${c.id}`}
              checked={on}
              label={c.label}
              onChange={() => onChange(on ? selected.filter((x) => x !== c.id) : [...selected, c.id])}
            />
          );
        })}
      </div>
    );
  } else if (type === 'numeric') {
    control = (
      <div className="relative max-w-xs">
        <input
          id={domId}
          type="number"
          inputMode="decimal"
          min={field.min_value ?? 0}
          max={field.max_value}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
          placeholder={field.placeholder || '0'}
          className={`${inputBase} ${borderCls} ${field.unit ? 'pr-16' : ''}`}
          {...a11y}
        />
        {field.unit && <span className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-sm text-iip-muted">{field.unit}</span>}
      </div>
    );
  } else if (type === 'date') {
    control = <input id={domId} type="date" value={value ?? ''} onChange={(e) => onChange(e.target.value)} className={`${inputBase} ${borderCls} max-w-xs`} {...a11y} />;
  } else {
    control = (
      <textarea
        id={domId}
        rows={4}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={field.placeholder || 'Escriba su respuesta…'}
        className={`${inputBase} ${borderCls}`}
        {...a11y}
      />
    );
  }

  const isGroup = type === 'boolean' || type === 'singlechoice' || type === 'multichoice';

  return (
    <div>
      {isGroup ? label : label && <label htmlFor={domId}>{label}</label>}
      {field.help_text && <p className="mb-2 text-xs text-iip-muted">{field.help_text}</p>}
      {control}
      {hasError && (
        <p id={errId} role="alert" className="mt-1.5 flex items-center gap-1.5 text-sm font-semibold text-rose-700">
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
          {error}
        </p>
      )}
    </div>
  );
};
