import { flattenForEntity } from '../utils/formTree';
import { isQuestionActive, selectedComponents } from '../utils/guidedForm';
import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import {
  CardEntryAnswer,
  EntitySubmission,
  FormField,
  FormSection,
  IIPForm,
  SubmissionItem,
  SubmissionValueAnswer,
} from '../types';
import { useApp } from './AppContext';
import { useAuth } from './AuthContext';
import { coreService } from '../services/coreService';

interface CardEntryItem {
  id: string;
  title: string;
  answers: Record<string, any>;
  /** Tarjeta (de la pregunta origen) de la que cuelga esta. */
  parent_id?: string | null;
}

interface FormSubmissionContextType {
  activeForm: IIPForm;
  activeSectionIndex: number;
  activeSection: FormSection | null;
  answers: Record<string, any>;
  cardEntries: Record<string, CardEntryItem[]>;
  errors: Record<string, string>;
  progress: number;
  isSubmitting: boolean;
  submitSuccess: boolean;
  lastSubmittedId: string | null;
  setActiveSectionIndex: (index: number) => void;
  nextSection: () => void;
  prevSection: () => void;
  setFieldValue: (fieldId: string, value: any) => void;
  addCardEntry: (questionId: string, templateId: string, initialTitle?: string, parentId?: string | null) => string;
  removeCardEntry: (questionId: string, entryId: string) => void;
  /** Cuántas tarjetas (directas e indirectas) se eliminarían junto con esta. */
  countDependentCards: (entryId: string) => number;
  setCardEntryFieldValue: (questionId: string, entryId: string, fieldId: string, value: any) => void;
  setCardEntryTitle: (questionId: string, entryId: string, title: string) => void;
  validateCurrentSection: () => boolean;
  validateAllSections: () => boolean;
  compileSubmissionPayload: () => SubmissionItem[];
  submitForm: () => Promise<EntitySubmission>;
  resetFormState: () => void;
  loadSubmissionForReview: (sub: EntitySubmission) => void;
  /** Componentes elegidos por la entidad (null = aún no eligió: aplican todos). */
  selectedComponentIds: string[] | null;
  setSelectedComponentIds: (ids: string[] | null) => void;
  /** Reemplaza los errores de validación mostrados (clave = field.id, `${card}_${field.id}` o question.id). */
  setFormErrors: (errors: Record<string, string>) => void;
  /** Guarda el borrador en el servidor (POST ?as_draft=true) y devuelve el id del radicado en borrador. */
  saveDraft: () => Promise<string>;
  isSavingDraft: boolean;
  lastDraftSavedAt: Date | null;
}

const FormSubmissionContext = createContext<FormSubmissionContextType | undefined>(undefined);

export const FormSubmissionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const {
    activeForm: rawActiveForm,
    addSubmission,
    actors,
    segments,
    updateAssignmentProgress,
    completeAssignmentSubmission,
  } = useApp();
  const { user } = useAuth();
  const [selectedComponentIds, setSelectedComponentIds] = useState<string[] | null>(null);
  const [isSavingDraft, setIsSavingDraft] = useState(false);
  const [lastDraftSavedAt, setLastDraftSavedAt] = useState<Date | null>(null);
  // Cada Variable agrupa las preguntas de sus Indicadores; solo cuentan los componentes elegidos.
  const activeForm = useMemo(
    () => flattenForEntity({ ...rawActiveForm, sections: selectedComponents(rawActiveForm, selectedComponentIds) }),
    [rawActiveForm, selectedComponentIds]
  );

  const [activeSectionIndex, setActiveSectionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [cardEntries, setCardEntries] = useState<Record<string, CardEntryItem[]>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [lastSubmittedId, setLastSubmittedId] = useState<string | null>(null);

  // Initialize draft from localStorage for this user/actor
  const storageKey = `iip_draft_${user?.actor_id || user?.id || 'guest'}_${activeForm.id}`;

  useEffect(() => {
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setAnswers(parsed.answers || {});
        setCardEntries(parsed.cardEntries || {});
      } catch {
        // start clean
      }
    } else {
      // Sin borrador local: se parte limpio (no arrastrar respuestas de otro formulario).
      setAnswers({});
      setCardEntries({});
      // Seed an initial empty card for repeatable templates if none exists
      activeForm.sections.forEach((sec) => {
        sec.questions?.forEach((q) => {
          // Las tarjetas vinculadas a otra pregunta solo existen colgando de una tarjeta origen.
          if (q.card_template.is_repeatable && !q.source_question_id) {
            setCardEntries((prev) => {
              if (!prev[q.id] || prev[q.id].length === 0) {
                return {
                  ...prev,
                  [q.id]: [
                    {
                      id: `card-${Date.now()}-1`,
                      title: 'Proyecto de Innovación #1',
                      answers: {},
                    },
                  ],
                };
              }
              return prev;
            });
          }
        });
      });
    }
  }, [storageKey, activeForm.id]);

  // Autosave draft
  useEffect(() => {
    if (Object.keys(answers).length > 0 || Object.keys(cardEntries).length > 0) {
      localStorage.setItem(storageKey, JSON.stringify({ answers, cardEntries }));
    }
  }, [answers, cardEntries, storageKey]);

  const activeSection = useMemo(() => {
    return activeForm.sections[activeSectionIndex] || activeForm.sections[0] || null;
  }, [activeForm, activeSectionIndex]);

  // Extract all fields in active form
  const allFields = useMemo(() => {
    const fieldsList: { field: FormField; questionId: string; isCard: boolean }[] = [];
    activeForm.sections.forEach((sec) => {
      sec.questions?.forEach((q) => {
        q.card_template.field_groups.forEach((fg) => {
          fg.fields.forEach((f) => {
            fieldsList.push({
              field: f,
              questionId: q.id,
              isCard: !!q.card_template.is_repeatable,
            });
          });
        });
      });
    });
    return fieldsList;
  }, [activeForm]);

  // Calculate progress percentage
  const progress = useMemo(() => {
    const nonCardRequiredFields = allFields.filter((item) => !item.isCard && item.field.is_required);
    if (nonCardRequiredFields.length === 0) return 100;

    let filledCount = 0;
    nonCardRequiredFields.forEach((item) => {
      const val = answers[item.field.id];
      if (val !== undefined && val !== null && val !== '') {
        filledCount++;
      }
    });

    // Check repeatable cards
    const cardQuestions = activeForm.sections
      .flatMap((s) => s.questions || [])
      .filter((q) => q.card_template.is_repeatable);

    let cardBonus = 0;
    let cardTotal = 0;
    cardQuestions.forEach((q) => {
      cardTotal += 1;
      const entries = cardEntries[q.id] || [];
      if (entries.length > 0) {
        // check if entry has some answers
        const hasFilled = entries.some((e) => Object.keys(e.answers).length >= 2);
        if (hasFilled) cardBonus += 1;
      }
    });

    const totalPoints = nonCardRequiredFields.length + cardTotal;
    const scoredPoints = filledCount + cardBonus;

    return Math.min(100, Math.round((scoredPoints / (totalPoints || 1)) * 100));
  }, [allFields, answers, cardEntries, activeForm]);

  const setFieldValue = useCallback((fieldId: string, value: any) => {
    setAnswers((prev) => ({ ...prev, [fieldId]: value }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[fieldId];
      return next;
    });
  }, []);

  const addCardEntry = useCallback((questionId: string, _templateId: string, initialTitle?: string, parentId?: string | null) => {
    const newId = `card-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
    setCardEntries((prev) => {
      const current = prev[questionId] || [];
      const count = current.length + 1;
      const entry: CardEntryItem = {
        id: newId,
        title: initialTitle || `Iniciativa de Innovación #${count}`,
        answers: {},
        parent_id: parentId ?? null,
      };
      return {
        ...prev,
        [questionId]: [...current, entry],
      };
    });
    return newId;
  }, []);

  /** Ids de las tarjetas que cuelgan (directa o indirectamente) de `entryId`. */
  const dependentsOf = (all: Record<string, CardEntryItem[]>, entryId: string): Set<string> => {
    const found = new Set<string>();
    let frontier = [entryId];
    while (frontier.length) {
      const next: string[] = [];
      Object.values(all).forEach((list) =>
        list.forEach((e) => {
          if (e.parent_id && frontier.includes(e.parent_id) && !found.has(e.id)) {
            found.add(e.id);
            next.push(e.id);
          }
        })
      );
      frontier = next;
    }
    return found;
  };

  const countDependentCards = useCallback((entryId: string) => dependentsOf(cardEntries, entryId).size, [cardEntries]);

  // Al quitar una tarjeta se quitan en cascada las que cuelgan de ella.
  const removeCardEntry = useCallback((questionId: string, entryId: string) => {
    setCardEntries((prev) => {
      const gone = dependentsOf(prev, entryId);
      gone.add(entryId);
      const next: Record<string, CardEntryItem[]> = {};
      (Object.entries(prev) as [string, CardEntryItem[]][]).forEach(([qid, list]) => {
        next[qid] = list.filter((e) => !gone.has(e.id));
      });
      return next;
    });
  }, []);

  const setCardEntryFieldValue = useCallback((questionId: string, entryId: string, fieldId: string, value: any) => {
    setCardEntries((prev) => {
      const current = prev[questionId] || [];
      const updated = current.map((item) => {
        if (item.id === entryId) {
          return {
            ...item,
            answers: {
              ...item.answers,
              [fieldId]: value,
            },
          };
        }
        return item;
      });
      return {
        ...prev,
        [questionId]: updated,
      };
    });
    setErrors((prev) => {
      const next = { ...prev };
      delete next[`${entryId}_${fieldId}`];
      return next;
    });
  }, []);

  const setCardEntryTitle = useCallback((questionId: string, entryId: string, title: string) => {
    setCardEntries((prev) => {
      const current = prev[questionId] || [];
      const updated = current.map((item) => (item.id === entryId ? { ...item, title } : item));
      return {
        ...prev,
        [questionId]: updated,
      };
    });
  }, []);

  const validateCurrentSection = useCallback((): boolean => {
    if (!activeSection) return true;
    const newErrors: Record<string, string> = {};

    activeSection.questions?.forEach((q) => {
      if (q.card_template.is_repeatable) {
        const entries = cardEntries[q.id] || [];
        if (q.card_template.min_entries && entries.length < q.card_template.min_entries) {
          newErrors[q.id] = `Debe registrar al menos ${q.card_template.min_entries} iniciativa(s).`;
        }
        // validate required fields inside each card entry
        entries.forEach((entry, idx) => {
          q.card_template.field_groups.forEach((fg) => {
            fg.fields.forEach((f) => {
              if (f.is_required) {
                const val = entry.answers[f.id];
                if (val === undefined || val === null || val === '') {
                  newErrors[`${entry.id}_${f.id}`] = `El campo "${f.label}" en la iniciativa #${idx + 1} es obligatorio.`;
                }
              }
            });
          });
        });
      } else {
        q.card_template.field_groups.forEach((fg) => {
          fg.fields.forEach((f) => {
            if (f.is_required) {
              const val = answers[f.id];
              if (val === undefined || val === null || val === '') {
                newErrors[f.id] = `El campo "${f.label}" es obligatorio.`;
              }
            }
          });
        });
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [activeSection, answers, cardEntries]);

  const validateAllSections = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};

    activeForm.sections.forEach((sec) => {
      sec.questions?.forEach((q) => {
        if (q.card_template.is_repeatable) {
          const entries = cardEntries[q.id] || [];
          if (q.card_template.min_entries && entries.length < q.card_template.min_entries) {
            newErrors[q.id] = `Debe registrar al menos ${q.card_template.min_entries} iniciativa(s).`;
          }
          entries.forEach((entry, idx) => {
            q.card_template.field_groups.forEach((fg) => {
              fg.fields.forEach((f) => {
                if (f.is_required) {
                  const val = entry.answers[f.id];
                  if (val === undefined || val === null || val === '') {
                    newErrors[`${entry.id}_${f.id}`] = `Iniciativa #${idx + 1}: ${f.label} es obligatorio.`;
                  }
                }
              });
            });
          });
        } else {
          q.card_template.field_groups.forEach((fg) => {
            fg.fields.forEach((f) => {
              if (f.is_required) {
                const val = answers[f.id];
                if (val === undefined || val === null || val === '') {
                  newErrors[f.id] = `${f.label} es obligatorio.`;
                }
              }
            });
          });
        }
      });
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [activeForm, answers, cardEntries]);

  /**
   * Compiles the typed payload for POST /submissions/forms/{id} (códigos = reference.field_types):
   * boolean / text / numeric / date -> { type, field_id, value }
   * single_choice -> { type, field_id, value: "choice-id" }
   * multi_choice  -> { type, field_id, value: ["choice-id", ...] }
   * file          -> { type, field_id, value: "file-id" }
   * card_entry    -> { type, field_id, question_id, card_template_id, title, card_index, answers: [...] }
   */
  const compileSubmissionPayload = useCallback((): SubmissionItem[] => {
    const toAnswer = (
      field: { id: string; field_type_code: string },
      rawVal: unknown
    ): SubmissionValueAnswer | null => {
      if (rawVal === undefined || rawVal === null || rawVal === '') return null;
      if (Array.isArray(rawVal) && rawVal.length === 0) return null;
      const field_id = field.id;
      switch (field.field_type_code) {
        case 'boolean':
          return { type: 'boolean', field_id, value: Boolean(rawVal) };
        case 'numeric':
          return { type: 'numeric', field_id, value: Number(rawVal) };
        case 'date':
          return { type: 'date', field_id, value: String(rawVal) };
        case 'singlechoice':
        case 'single_choice':
          return { type: 'single_choice', field_id, value: String(rawVal) };
        case 'multichoice':
        case 'multi_choice':
          return {
            type: 'multi_choice',
            field_id,
            value: (Array.isArray(rawVal) ? rawVal : [rawVal]).map(String),
          };
        case 'file':
          return { type: 'file', field_id, value: String(rawVal) };
        case 'text':
        default:
          return { type: 'text', field_id, value: String(rawVal) };
      }
    };

    const payload: SubmissionItem[] = [];

    activeForm.sections.forEach((sec) => {
      sec.questions?.forEach((q) => {
        if (!isQuestionActive(q, sec.questions ?? [], answers)) return;
        if (q.card_template.is_repeatable) {
          const entries = cardEntries[q.id] || [];
          entries.forEach((entry, index) => {
            const nestedAnswers: SubmissionValueAnswer[] = [];
            q.card_template.field_groups.forEach((fg) => {
              fg.fields.forEach((field) => {
                const a = toAnswer(field, entry.answers[field.id]);
                if (a) nestedAnswers.push(a);
              });
            });

            const cardEntryPayload: CardEntryAnswer = {
              type: 'card_entry',
              field_id: q.card_template.field_groups[0]?.fields[0]?.id || 'field-title',
              question_id: q.id,
              card_template_id: q.card_template.id,
              title: entry.title || `Iniciativa #${index + 1}`,
              card_index: index,
              ref: entry.id,
              ...(entry.parent_id ? { parent_ref: entry.parent_id } : {}),
              answers: nestedAnswers,
            };
            payload.push(cardEntryPayload);
          });
        } else {
          q.card_template.field_groups.forEach((fg) => {
            fg.fields.forEach((field) => {
              const a = toAnswer(field, answers[field.id]);
              if (a) payload.push(a);
            });
          });
        }
      });
    });

    return payload;
  }, [activeForm, answers, cardEntries]);

  const submitForm = async (): Promise<EntitySubmission> => {
    setIsSubmitting(true);
    try {
      const payload = compileSubmissionPayload();

      // Dispatch to the core service
      const saved = await coreService.submitForm(activeForm.id, payload);

      const targetActor = actors.find((a) => a.id === user?.actor_id) || actors[0];
      const targetSegment = segments.find((s) => s.id === targetActor?.actor_segment_id);

      const newSubmission: EntitySubmission = {
        id: saved.submission_id,
        form_id: activeForm.id,
        form_code: activeForm.code,
        form_title: activeForm.label,
        actor_id: targetActor?.id || 'act-001',
        actor_label: targetActor?.label || user?.actor_label || 'Entidad Pública',
        actor_segment_label: targetSegment?.label || 'Nivel Central',
        submitted_at: new Date().toISOString(),
        status: 'submitted',
        completion_percentage: 100,
        payload,
        raw_answers: { ...answers },
        card_entries: { ...cardEntries },
      };

      addSubmission(newSubmission);
      // El radicado es el id que asignó el servidor (no se inventa un número local).
      const radNumber = `RAD-${newSubmission.id.slice(0, 8).toUpperCase()}`;
      completeAssignmentSubmission(
        newSubmission.actor_id,
        activeForm.id,
        newSubmission.id,
        radNumber,
        newSubmission.score
      );

      setLastSubmittedId(newSubmission.id);
      setSubmitSuccess(true);
      localStorage.removeItem(storageKey);
      return newSubmission;
    } finally {
      setIsSubmitting(false);
    }
  };

  const saveDraft = async (): Promise<string> => {
    setIsSavingDraft(true);
    try {
      const saved = await coreService.submitForm(activeForm.id, compileSubmissionPayload(), true);
      setLastDraftSavedAt(new Date());
      return saved.submission_id;
    } finally {
      setIsSavingDraft(false);
    }
  };

  const nextSection = () => {
    if (activeSectionIndex < activeForm.sections.length - 1) {
      setActiveSectionIndex((prev) => prev + 1);
    }
  };

  const prevSection = () => {
    if (activeSectionIndex > 0) {
      setActiveSectionIndex((prev) => prev - 1);
    }
  };

  const resetFormState = () => {
    setAnswers({});
    setCardEntries({});
    setErrors({});
    setSubmitSuccess(false);
    setLastSubmittedId(null);
    setActiveSectionIndex(0);
    localStorage.removeItem(storageKey);
  };

  const loadSubmissionForReview = (sub: EntitySubmission) => {
    setAnswers(sub.raw_answers || {});
    if (sub.card_entries) {
      setCardEntries(sub.card_entries);
    }
    setActiveSectionIndex(0);
  };

  return (
    <FormSubmissionContext.Provider
      value={{
        activeForm,
        activeSectionIndex,
        activeSection,
        answers,
        cardEntries,
        errors,
        progress,
        isSubmitting,
        submitSuccess,
        lastSubmittedId,
        setActiveSectionIndex,
        nextSection,
        prevSection,
        setFieldValue,
        addCardEntry,
        removeCardEntry,
        countDependentCards,
        setCardEntryFieldValue,
        setCardEntryTitle,
        validateCurrentSection,
        validateAllSections,
        compileSubmissionPayload,
        submitForm,
        resetFormState,
        loadSubmissionForReview,
        selectedComponentIds,
        setSelectedComponentIds,
        setFormErrors: setErrors,
        saveDraft,
        isSavingDraft,
        lastDraftSavedAt,
      }}
    >
      {children}
    </FormSubmissionContext.Provider>
  );
};

export const useFormSubmission = () => {
  const context = useContext(FormSubmissionContext);
  if (!context) {
    throw new Error('useFormSubmission must be used within a FormSubmissionProvider');
  }
  return context;
};
