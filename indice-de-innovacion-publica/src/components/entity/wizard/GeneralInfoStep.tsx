import React from 'react';
import { ArrowRight, Building2, CalendarClock, FileText, StickyNote } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { EntityAssignment, IIPForm } from '../../../types';
import { countIndicators, countVariables } from '../../../utils/formTree';
import { formatDate } from '../EntityFormsView';
import { TermsAndConditions } from './TermsAndConditions';

const Item: React.FC<{ icon: React.ElementType; label: string; children: React.ReactNode }> = ({ icon: Icon, label, children }) => (
  <div className="flex items-start gap-3 rounded-2xl bg-iip-bg p-4">
    <Icon className="mt-0.5 h-5 w-5 shrink-0 text-iip-navy" aria-hidden="true" />
    <div className="min-w-0">
      <dt className="text-xs font-bold uppercase tracking-wide text-iip-muted">{label}</dt>
      <dd className="mt-0.5 text-[15px] font-semibold text-iip-ink">{children}</dd>
    </div>
  </div>
);

/** Etapa 1: contexto del diligenciamiento (entidad, formulario, plazos). */
export const GeneralInfoStep: React.FC<{ assignment: EntityAssignment; form: IIPForm; onContinue: () => void }> = ({ assignment, form, onContinue }) => {
  const { user } = useAuth();
  return (
    <section aria-labelledby="info-title" className="mx-auto w-full max-w-4xl rounded-3xl border border-iip-line bg-white p-5 shadow-sm sm:p-8">
      <h2 id="info-title" className="text-2xl font-extrabold text-iip-ink">{form.label}</h2>
      {form.description && <p className="mt-2 text-[15px] leading-relaxed text-iip-muted">{form.description}</p>}

      <dl className="mt-6 grid gap-3 sm:grid-cols-2">
        <Item icon={Building2} label="Entidad">{assignment.actor_label || user?.actor_label || '—'}</Item>
        <Item icon={FileText} label="Formulario">{form.code}{form.year ? ` · ${form.year}` : ''}</Item>
        <Item icon={CalendarClock} label="Fecha límite">{formatDate(assignment.due_date)}</Item>
        <Item icon={FileText} label="Estructura">{form.sections.length} componente(s) · {countVariables(form)} variable(s) · {countIndicators(form)} indicador(es)</Item>
        {assignment.notes && <div className="sm:col-span-2"><Item icon={StickyNote} label="Nota del administrador">{assignment.notes}</Item></div>}
      </dl>

      <div className="mt-6 rounded-2xl bg-iip-yellow-50 p-4 text-sm leading-relaxed text-iip-ink">
        Responda con la información oficial de su entidad. Puede <strong>guardar un borrador</strong> en cualquier momento y continuar después; el formulario solo se envía en la etapa final.
      </div>

      <TermsAndConditions />

      <p className="mt-4 text-sm font-semibold text-iip-ink">
        Al continuar, su entidad declara que leyó y acepta los términos y condiciones y el tratamiento de la información descritos arriba.
      </p>

      <div className="mt-4 flex justify-end">
        <button type="button" onClick={onContinue} className="iip-focus flex items-center gap-2 rounded-xl bg-iip-yellow px-6 py-3 text-[15px] font-extrabold text-iip-ink shadow-sm hover:bg-iip-yellow-600">
          Aceptar y elegir componentes <ArrowRight className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>
    </section>
  );
};
