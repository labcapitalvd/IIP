import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AlertCircle, CheckCircle2, FileText, Loader2 } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { useApp } from '../../../context/AppContext';
import { useFormSubmission } from '../../../context/FormSubmissionContext';
import { coreService } from '../../../services/coreService';
import { EntityAssignment } from '../../../types';
import { buildIndicatorRefs, progressOf, validateIndicator } from '../../../utils/guidedForm';
import { SubmissionReviewModal } from '../SubmissionReviewModal';
import { AnswersReport } from './AnswersReport';
import { ComponentSelectionStep } from './ComponentSelectionStep';
import { ComponentSidebar } from './ComponentSidebar';
import { GeneralInfoStep } from './GeneralInfoStep';
import { HelpPanel } from './HelpPanel';
import { IndicatorForm } from './IndicatorForm';
import { ReopenSection } from './ReopenSection';
import { ReviewStep } from './ReviewStep';
import { Stepper, WizardStage } from './Stepper';
import { WizardFooter } from './WizardFooter';
import { WizardHeader } from './WizardHeader';

interface Props {
  assignment: EntityAssignment;
  onExit: () => void;
  /** La selección de componentes quedó guardada en el servidor. */
  onSelectionSaved: (assignmentId: string, ids: string[]) => void;
  /** Cambió el avance en el servidor (borrador guardado o formulario enviado). */
  onProgressChanged: () => void;
}

const posKey = (id: string) => `iip_wizard_pos_${id}`;
const readPos = (id: string) => {
  try {
    return Number(localStorage.getItem(posKey(id))) || 0;
  } catch {
    return 0;
  }
};

const Centered: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-iip-bg p-6 text-center text-iip-ink">{children}</div>
);

export const GuidedDiagnostic: React.FC<Props> = ({ assignment, onExit, onSelectionSaved, onProgressChanged }) => {
  const { activeForm: rawForm, setActiveFormById, isLoadingData } = useApp();
  const ctx = useFormSubmission();
  const { answers, cardEntries, selectedComponentIds, setSelectedComponentIds } = ctx;

  const ready = rawForm.id === assignment.form_id;
  const [synced, setSynced] = useState(false);
  const [stage, setStage] = useState<WizardStage>('info');
  const [index, setIndex] = useState(0);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [showAnswers, setShowAnswers] = useState(false);
  const { user } = useAuth();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const latest = useRef({ answers, cardEntries });
  latest.current = { answers, cardEntries };

  // 1) Activar el formulario asignado.
  useEffect(() => {
    setSynced(false);
    setActiveFormById(assignment.form_id);
  }, [assignment.form_id, setActiveFormById]);

  // 2) Cuando está cargado: aplicar la selección guardada y decidir la etapa inicial.
  useEffect(() => {
    if (!ready || synced) return;
    const valid = (assignment.selected_component_ids ?? []).filter((id) => rawForm.sections.some((c) => c.id === id));
    setSelectedComponentIds(valid.length ? valid : null);
    setStage(assignment.status === 'submitted' ? 'done' : valid.length ? 'fill' : 'info');
    setIndex(readPos(assignment.id));
    setSynced(true);
  }, [ready, synced, assignment, rawForm, setSelectedComponentIds]);

  // 3) Borrador del servidor: si no hay nada local (otro navegador/equipo), se restaura.
  useEffect(() => {
    if (!synced || assignment.status === 'pending' || !assignment.submission_id) return;
    let alive = true;
    setRestoring(true);
    coreService
      .getSubmission(assignment.submission_id)
      .then((sub) => {
        const empty = Object.keys(latest.current.answers).length === 0 && Object.keys(latest.current.cardEntries).length === 0;
        if (alive && empty) ctx.loadSubmissionForReview(sub);
      })
      .catch(() => undefined) // sin borrador remoto se empieza limpio
      .finally(() => alive && setRestoring(false));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [synced, assignment.id]);

  const refs = useMemo(() => buildIndicatorRefs(rawForm, selectedComponentIds), [rawForm, selectedComponentIds]);
  const allRefs = useMemo(() => buildIndicatorRefs(rawForm, null), [rawForm]);
  const state = useMemo(() => ({ answers, cardEntries }), [answers, cardEntries]);
  const overall = useMemo(() => progressOf(refs, state), [refs, state]);
  const safeIndex = Math.min(index, Math.max(refs.length - 1, 0));
  const current = refs[safeIndex];
  const hasSelection = !!selectedComponentIds?.length;

  const componentNumber = useCallback((id: string) => rawForm.sections.findIndex((c) => c.id === id) + 1, [rawForm]);

  const go = useCallback(
    (i: number) => {
      const next = Math.max(0, Math.min(i, refs.length - 1));
      setIndex(next);
      ctx.setFormErrors({});
      setStage('fill');
      try {
        localStorage.setItem(posKey(assignment.id), String(next));
      } catch {
        /* sin almacenamiento local: solo no se recuerda la posición */
      }
      window.scrollTo({ top: 0 });
      requestAnimationFrame(() => headingRef.current?.focus());
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [refs.length, assignment.id]
  );

  const handleNext = () => {
    if (!current) return;
    const errs = validateIndicator(current.indicator, state);
    ctx.setFormErrors(errs);
    if (Object.keys(errs).length) {
      requestAnimationFrame(() => (document.querySelector('[aria-invalid="true"]') as HTMLElement | null)?.focus?.() ?? undefined);
      return;
    }
    if (safeIndex >= refs.length - 1) {
      setStage('review');
      window.scrollTo({ top: 0 });
    } else go(safeIndex + 1);
  };

  const handleSave = async () => {
    setSaveError(null);
    try {
      await ctx.saveDraft();
      onProgressChanged();
    } catch (e: any) {
      setSaveError(e?.message || 'No se pudo guardar el borrador.');
    }
  };

  const confirmSelection = async (ids: string[]) => {
    await coreService.selectAssignmentComponents(assignment.id, ids);
    setSelectedComponentIds(ids);
    onSelectionSaved(assignment.id, ids);
    const nextRefs = buildIndicatorRefs(rawForm, ids);
    const keep = current ? nextRefs.findIndex((r) => r.indicator.id === current.indicator.id) : -1;
    setIndex(keep >= 0 ? keep : 0);
    setStage('fill');
    window.scrollTo({ top: 0 });
  };

  const canGo = (s: WizardStage) => stage !== 'done' && (s === 'info' || s === 'components' || (hasSelection && (s === 'fill' || s === 'review')));
  const onStepperGo = (s: WizardStage) => (s === 'fill' ? go(safeIndex) : setStage(s));

  // ---- Estados de carga / error ----
  if (!ready || !synced) {
    if (!ready && !isLoadingData)
      return (
        <Centered>
          <AlertCircle className="h-10 w-10 text-rose-600" />
          <p className="font-semibold">No se pudo cargar el formulario asignado.</p>
          <button type="button" onClick={onExit} className="iip-focus rounded-xl bg-iip-yellow px-5 py-2.5 font-bold">Volver a mis formularios</button>
        </Centered>
      );
    return (
      <Centered>
        <Loader2 className="h-10 w-10 animate-spin text-iip-navy" />
        <p className="font-semibold">Cargando formulario…</p>
      </Centered>
    );
  }

  const effectiveStage: WizardStage = ctx.submitSuccess ? 'done' : stage;

  return (
    <div className="flex min-h-screen flex-col bg-iip-bg font-sans text-iip-ink">
      <WizardHeader onExit={onExit} />
      <Stepper current={effectiveStage} canGo={canGo} onGo={onStepperGo} />

      <main className="mx-auto w-full max-w-[1500px] flex-1 px-4 py-4 sm:px-6">
        {restoring && (
          <p role="status" className="mb-3 flex items-center gap-2 text-sm text-iip-muted"><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Recuperando su borrador…</p>
        )}

        {effectiveStage === 'info' && <GeneralInfoStep assignment={assignment} form={rawForm} onContinue={() => setStage('components')} />}

        {effectiveStage === 'components' && (
          <ComponentSelectionStep components={rawForm.sections} initialSelected={selectedComponentIds ?? []} state={state} onConfirm={confirmSelection} />
        )}

        {effectiveStage === 'fill' &&
          (current ? (
            <div className="grid gap-4 lg:grid-cols-[300px_minmax(0,1fr)_340px] xl:grid-cols-[320px_minmax(0,1fr)_380px]">
              <ComponentSidebar refs={refs} current={current} state={state} componentNumber={componentNumber} onGo={go} />

              <section aria-labelledby="indicator-title" className="rounded-3xl border border-iip-line bg-white p-5 shadow-sm sm:p-7">
                <div className="flex flex-wrap items-center gap-3 border-b border-iip-line pb-4">
                  <span className="rounded-xl bg-iip-yellow px-3 py-1.5 text-base font-extrabold text-iip-ink">
                    Variable {(current.component.children ?? []).findIndex((v) => v.id === current.variable.id) + 1}
                  </span>
                  <h2 className="text-lg font-extrabold leading-snug sm:text-xl">{current.variable.label}</h2>
                </div>

                <h3 id="indicator-title" ref={headingRef} tabIndex={-1} className="mt-5 text-lg font-extrabold leading-snug outline-none">
                  Indicador {allRefs.findIndex((r) => r.indicator.id === current.indicator.id) + 1}. {current.indicator.label}
                </h3>
                {current.indicator.description && <p className="mt-2 text-[15px] leading-relaxed text-iip-muted">{current.indicator.description}</p>}

                <div className="mt-6">
                  <IndicatorForm key={current.indicator.id} indicator={current.indicator} />
                </div>
              </section>

              <HelpPanel component={current.component} variable={current.variable} indicator={current.indicator} />
            </div>
          ) : (
            <p className="rounded-2xl bg-white p-6 text-center text-iip-muted">Los componentes elegidos no tienen indicadores por responder.</p>
          ))}

        {effectiveStage === 'review' && (
          <ReviewStep refs={refs} state={state} componentNumber={componentNumber} onEdit={go} onBack={() => go(safeIndex)} onSubmit={() => setShowReviewModal(true)} />
        )}

        {effectiveStage === 'done' && (
          <section className="mx-auto max-w-2xl rounded-3xl border border-iip-line bg-white p-8 text-center shadow-sm" aria-live="polite">
            <CheckCircle2 className="mx-auto h-16 w-16 text-iip-green" aria-hidden="true" />
            <h2 className="mt-4 text-2xl font-extrabold">{ctx.submitSuccess ? '¡Formulario enviado!' : 'Este formulario ya fue enviado'}</h2>
            <p className="mt-2 text-[15px] text-iip-muted">
              {ctx.submitSuccess
                ? 'La información de su entidad quedó registrada en la plataforma del Índice de Innovación Pública.'
                : 'Su entidad ya radicó este formulario; no es posible modificarlo.'}
            </p>
            {ctx.lastSubmittedId && <p className="mt-3 font-mono text-xs text-iip-muted">Radicado: RAD-{ctx.lastSubmittedId.slice(0, 8).toUpperCase()}</p>}
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => setShowAnswers(true)}
              disabled={restoring}
              className="iip-focus flex items-center gap-2 rounded-xl bg-iip-navy px-6 py-3 text-[15px] font-extrabold text-white hover:bg-iip-navy-700 disabled:opacity-60"
            >
              {restoring ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> : <FileText className="h-5 w-5" aria-hidden="true" />}
              Ver todas las respuestas
            </button>
            <button
              type="button"
              onClick={() => {
                if (ctx.submitSuccess) {
                  ctx.resetFormState();
                  onProgressChanged();
                }
                onExit();
              }}
              className="iip-focus rounded-xl bg-iip-yellow px-6 py-3 text-[15px] font-extrabold hover:bg-iip-yellow-600"
            >
              Volver a mis formularios
            </button>
            </div>
            {!ctx.submitSuccess && <ReopenSection assignment={assignment} onChanged={onProgressChanged} />}
          </section>
        )}
      </main>

      {effectiveStage === 'fill' && current && (
        <WizardFooter
          position={safeIndex + 1}
          total={refs.length}
          progress={overall}
          isFirst={safeIndex === 0}
          isLast={safeIndex === refs.length - 1}
          isSaving={ctx.isSavingDraft}
          savedAt={ctx.lastDraftSavedAt}
          saveError={saveError}
          onPrev={() => go(safeIndex - 1)}
          onNext={handleNext}
          onSave={handleSave}
        />
      )}

      {showAnswers && (
        <AnswersReport form={rawForm} selectedIds={selectedComponentIds} state={state} entityLabel={user?.actor_label || assignment.actor_label || 'Entidad pública'} onClose={() => setShowAnswers(false)} />
      )}

      <SubmissionReviewModal isOpen={showReviewModal} onClose={() => setShowReviewModal(false)} onSuccess={() => setShowReviewModal(false)} />
    </div>
  );
};
