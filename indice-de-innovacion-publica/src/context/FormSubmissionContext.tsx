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
  addCardEntry: (questionId: string, templateId: string, initialTitle?: string) => string;
  removeCardEntry: (questionId: string, entryId: string) => void;
  setCardEntryFieldValue: (questionId: string, entryId: string, fieldId: string, value: any) => void;
  setCardEntryTitle: (questionId: string, entryId: string, title: string) => void;
  validateCurrentSection: () => boolean;
  validateAllSections: () => boolean;
  compileSubmissionPayload: () => SubmissionItem[];
  submitForm: () => Promise<EntitySubmission>;
  resetFormState: () => void;
  loadSubmissionForReview: (sub: EntitySubmission) => void;
}

const FormSubmissionContext = createContext<FormSubmissionContextType | undefined>(undefined);

export const FormSubmissionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const {
    activeForm,
    addSubmission,
    actors,
    segments,
    updateAssignmentProgress,
    completeAssignmentSubmission,
  } = useApp();
  const { user } = useAuth();

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
      // Seed an initial empty card for repeatable templates if none exists
      activeForm.sections.forEach((sec) => {
        sec.questions?.forEach((q) => {
          if (q.card_template.is_repeatable) {
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

  const addCardEntry = useCallback((questionId: string, _templateId: string, initialTitle?: string) => {
    const newId = `card-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
    setCardEntries((prev) => {
      const current = prev[questionId] || [];
      const count = current.length + 1;
      const entry: CardEntryItem = {
        id: newId,
        title: initialTitle || `Iniciativa de Innovación #${count}`,
        answers: {},
      };
      return {
        ...prev,
        [questionId]: [...current, entry],
      };
    });
    return newId;
  }, []);

  const removeCardEntry = useCallback((questionId: string, entryId: string) => {
    setCardEntries((prev) => {
      const current = prev[questionId] || [];
      return {
        ...prev,
        [questionId]: current.filter((e) => e.id !== entryId),
      };
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
   * Compiles typed submission payload strictly adhering to backend specification:
   * "boolean" -> { type: "boolean", field_id: "...", value: true }
   * "text" -> { type: "text", field_id: "...", value: "string" }
   * "numeric" -> { type: "numeric", field_id: "...", value: 12.5 }
   * "date" -> { type: "date", field_id: "...", value: "2026-08-20" }
   * "singlechoice" -> { type: "singlechoice", field_id: "...", value: "choice-id" }
   * "card_entry" -> { type: "card_entry", field_id, question_id, card_template_id, title, card_index, answers: [...] }
   */
  const compileSubmissionPayload = useCallback((): SubmissionItem[] => {
    const payload: SubmissionItem[] = [];

    activeForm.sections.forEach((sec) => {
      sec.questions?.forEach((q) => {
        if (q.card_template.is_repeatable) {
          const entries = cardEntries[q.id] || [];
          entries.forEach((entry, index) => {
            const nestedAnswers: SubmissionValueAnswer[] = [];

            q.card_template.field_groups.forEach((fg) => {
              fg.fields.forEach((field) => {
                const rawVal = entry.answers[field.id];
                if (rawVal === undefined || rawVal === null || rawVal === '') return;

                switch (field.field_type_code) {
                  case 'boolean':
                    nestedAnswers.push({
                      type: 'boolean',
                      field_id: field.id,
                      value: Boolean(rawVal),
                    });
                    break;
                  case 'numeric':
                    nestedAnswers.push({
                      type: 'numeric',
                      field_id: field.id,
                      value: Number(rawVal),
                    });
                    break;
                  case 'date':
                    nestedAnswers.push({
                      type: 'date',
                      field_id: field.id,
                      value: String(rawVal),
                    });
                    break;
                  case 'singlechoice':
                    nestedAnswers.push({
                      type: 'singlechoice',
                      field_id: field.id,
                      value: String(rawVal),
                    });
                    break;
                  case 'text':
                  default:
                    nestedAnswers.push({
                      type: 'text',
                      field_id: field.id,
                      value: String(rawVal),
                    });
                    break;
                }
              });
            });

            const cardEntryPayload: CardEntryAnswer = {
              type: 'card_entry',
              field_id: q.card_template.field_groups[0]?.fields[0]?.id || 'field-title',
              question_id: q.id,
              card_template_id: q.card_template.id,
              title: entry.title || `Iniciativa #${index + 1}`,
              card_index: index,
              answers: nestedAnswers,
            };

            payload.push(cardEntryPayload);
          });
        } else {
          // Standard question / single card template fields
          q.card_template.field_groups.forEach((fg) => {
            fg.fields.forEach((field) => {
              const rawVal = answers[field.id];
              if (rawVal === undefined || rawVal === null || rawVal === '') return;

              switch (field.field_type_code) {
                case 'boolean':
                  payload.push({
                    type: 'boolean',
                    field_id: field.id,
                    value: Boolean(rawVal),
                  });
                  break;
                case 'numeric':
                  payload.push({
                    type: 'numeric',
                    field_id: field.id,
                    value: Number(rawVal),
                  });
                  break;
                case 'date':
                  payload.push({
                    type: 'date',
                    field_id: field.id,
                    value: String(rawVal),
                  });
                  break;
                case 'singlechoice':
                  payload.push({
                    type: 'singlechoice',
                    field_id: field.id,
                    value: String(rawVal),
                  });
                  break;
                case 'text':
                default:
                  payload.push({
                    type: 'text',
                    field_id: field.id,
                    value: String(rawVal),
                  });
                  break;
              }
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

      // Dispatch to real core service or mock
      await coreService.submitForm(activeForm.id, payload);

      const targetActor = actors.find((a) => a.id === user?.actor_id) || actors[0];
      const targetSegment = segments.find((s) => s.id === targetActor?.actor_segment_id);

      const newSubmission: EntitySubmission = {
        id: `sub-${Date.now()}`,
        form_id: activeForm.id,
        form_code: activeForm.code,
        form_title: activeForm.label,
        actor_id: targetActor?.id || 'act-001',
        actor_label: targetActor?.label || user?.actor_label || 'Entidad Pública',
        actor_segment_label: targetSegment?.label || 'Nivel Central',
        submitted_by: user?.username || 'usuario.entidad',
        submitted_at: new Date().toISOString(),
        status: 'submitted',
        score: Math.min(100, Math.max(50, Math.round(progress * 0.95 + Math.random() * 5))),
        completion_percentage: 100,
        payload,
        raw_answers: { ...answers },
        card_entries: { ...cardEntries },
      };

      addSubmission(newSubmission);
      const radNumber = `RAD-IIP-${new Date().getFullYear()}-${Math.floor(100000 + Math.random() * 900000)}`;
      completeAssignmentSubmission(
        newSubmission.actor_id,
        activeForm.id,
        newSubmission.id,
        radNumber,
        newSubmission.score || 85
      );

      setLastSubmittedId(newSubmission.id);
      setSubmitSuccess(true);
      localStorage.removeItem(storageKey);
      return newSubmission;
    } finally {
      setIsSubmitting(false);
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
        setCardEntryFieldValue,
        setCardEntryTitle,
        validateCurrentSection,
        validateAllSections,
        compileSubmissionPayload,
        submitForm,
        resetFormState,
        loadSubmissionForReview,
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
