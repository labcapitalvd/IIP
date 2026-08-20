import React, { useState, useEffect } from 'react';
import {
  IIPForm,
  FormSection,
  FormQuestion,
  FormField,
  FieldChoice,
  FieldGroup,
} from '../../types';
import {
  X,
  Plus,
  Trash2,
  Layers,
  HelpCircle,
  Sparkles,
  Building2,
  Cpu,
  Rocket,
  CheckCircle2,
  AlertCircle,
  Eye,
  Sliders,
  ChevronDown,
  ChevronRight,
  MoveUp,
  MoveDown,
  FileText,
  Check,
} from 'lucide-react';

interface FormBuilderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (form: IIPForm) => Promise<void>;
  initialForm?: IIPForm | null;
}

const ICON_OPTIONS = [
  { label: 'Capacidades / Institución (Building2)', value: 'Building2' },
  { label: 'Cultura / Innovación (Sparkles)', value: 'Sparkles' },
  { label: 'Tecnología / Datos (Cpu)', value: 'Cpu' },
  { label: 'Proyectos / Impacto (Rocket)', value: 'Rocket' },
  { label: 'Estrategia / Capas (Layers)', value: 'Layers' },
];

const getDefaultSections = (): FormSection[] => [
  {
    id: `sec-${Date.now()}-1`,
    code: 'DIM_1_CAPACIDADES',
    label: 'Dimensión 1: Capacidades Institucionales para la Innovación',
    description: 'Evalúa la existencia de estructura formal, equipo técnico y asignación presupuestal.',
    order_index: 1,
    icon_name: 'Building2',
    questions: [
      {
        id: `q-${Date.now()}-1`,
        code: 'Q_ESTRUCTURA_TALENTO',
        label: 'Estructura Organizacional y Talento Humano',
        card_template: {
          id: `ct-${Date.now()}-1`,
          code: 'CT_ESTRUCTURA',
          label: 'Capacidades de Talento e Instancias',
          field_groups: [
            {
              id: `fg-${Date.now()}-1`,
              code: 'FG_TALENTO',
              label: 'Instancias y Roles',
              fields: [
                {
                  id: `f-${Date.now()}-1`,
                  code: 'TIENE_INSTANCIA_FORMAL',
                  label: '¿La entidad cuenta con una instancia o equipo formalmente designado para liderar innovación pública?',
                  field_type_id: 'ft-bool',
                  field_type_code: 'boolean',
                  is_required: true,
                  help_text: 'Marque Sí si existe resolución o decreto interno de creación.',
                },
              ],
            },
          ],
        },
      },
    ],
  },
];

export const FormBuilderModal: React.FC<FormBuilderModalProps> = ({
  isOpen,
  onClose,
  onSave,
  initialForm,
}) => {
  const isEditing = !!initialForm;

  // Form Basic Info State
  const [label, setLabel] = useState(
    initialForm?.label || 'Índice de Innovación Pública - Medición Anual Distrital 2026'
  );
  const [code, setCode] = useState(initialForm?.code || `IIP_${new Date().getFullYear()}_V1`);
  const [description, setDescription] = useState(
    initialForm?.description ||
      'Instrumento técnico de diagnóstico y recolección de evidencias para medir las capacidades, cultura, prácticas e iniciativas de innovación pública en las entidades distritales.'
  );
  const [year, setYear] = useState(initialForm?.year || new Date().getFullYear());
  const [version, setVersion] = useState(initialForm?.version || '1.0');
  const [isActive, setIsActive] = useState(initialForm?.is_active ?? true);

  // Form Sections State
  const [sections, setSections] = useState<FormSection[]>(() => {
    if (initialForm?.sections && initialForm.sections.length > 0) {
      return JSON.parse(JSON.stringify(initialForm.sections));
    }
    return getDefaultSections();
  });

  const [activeSectionIndex, setActiveSectionIndex] = useState(0);
  const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Synchronize state whenever modal is opened or initialForm changes
  useEffect(() => {
    if (isOpen) {
      if (initialForm) {
        setLabel(initialForm.label || '');
        setCode(initialForm.code || '');
        setDescription(initialForm.description || '');
        setYear(initialForm.year || new Date().getFullYear());
        setVersion(initialForm.version || '1.0');
        setIsActive(initialForm.is_active ?? true);
        if (initialForm.sections && initialForm.sections.length > 0) {
          setSections(JSON.parse(JSON.stringify(initialForm.sections)));
        } else {
          setSections(getDefaultSections());
        }
      } else {
        setLabel('Índice de Innovación Pública - Medición Anual Distrital 2026');
        setCode(`IIP_${new Date().getFullYear()}_V1`);
        setDescription(
          'Instrumento técnico de diagnóstico y recolección de evidencias para medir las capacidades, cultura, prácticas e iniciativas de innovación pública en las entidades distritales.'
        );
        setYear(new Date().getFullYear());
        setVersion('1.0');
        setIsActive(true);
        setSections(getDefaultSections());
      }
      setActiveSectionIndex(0);
      setActiveQuestionIndex(0);
      setIsPreviewMode(false);
      setErrorMsg(null);
    }
  }, [initialForm, isOpen]);

  if (!isOpen) return null;

  // Add Section
  const handleAddSection = () => {
    const newIdx = sections.length + 1;
    const newSec: FormSection = {
      id: `sec-${Date.now()}-${newIdx}`,
      code: `DIM_${newIdx}_NUEVA`,
      label: `Dimensión ${newIdx}: Nueva Dimensión de Evaluación`,
      description: 'Descripción del alcance de esta dimensión del IIP.',
      order_index: newIdx,
      icon_name: 'Sparkles',
      questions: [
        {
          id: `q-${Date.now()}-1`,
          code: `Q_DIM${newIdx}_01`,
          label: 'Pregunta Principal de Diagnóstico',
          card_template: {
            id: `ct-${Date.now()}-1`,
            code: `CT_DIM${newIdx}_01`,
            label: 'Grupo de Criterios',
            field_groups: [
              {
                id: `fg-${Date.now()}-1`,
                code: `FG_DIM${newIdx}_01`,
                label: 'Criterios de Evaluación',
                fields: [
                  {
                    id: `f-${Date.now()}-1`,
                    code: `CAMPO_01`,
                    label: '¿La entidad cuenta con procesos documentados para esta variable?',
                    field_type_id: 'ft-bool',
                    field_type_code: 'boolean',
                    is_required: true,
                  },
                ],
              },
            ],
          },
        },
      ],
    };
    setSections([...sections, newSec]);
    setActiveSectionIndex(sections.length);
    setActiveQuestionIndex(0);
  };

  // Move Section Up/Down
  const handleMoveSection = (idx: number, direction: 'up' | 'down') => {
    if ((direction === 'up' && idx === 0) || (direction === 'down' && idx === sections.length - 1)) return;
    const targetIdx = direction === 'up' ? idx - 1 : idx + 1;
    const updated = [...sections];
    const temp = updated[idx];
    updated[idx] = updated[targetIdx];
    updated[targetIdx] = temp;
    setSections(updated);
    setActiveSectionIndex(targetIdx);
  };

  // Remove Section
  const handleRemoveSection = (secIdx: number) => {
    if (sections.length <= 1) {
      alert('El formulario debe tener al menos 1 dimensión.');
      return;
    }
    const updated = sections.filter((_, idx) => idx !== secIdx);
    setSections(updated);
    setActiveSectionIndex(Math.max(0, secIdx - 1));
    setActiveQuestionIndex(0);
  };

  // Add Question to active section
  const handleAddQuestion = () => {
    const curSec = sections[activeSectionIndex];
    if (!curSec) return;
    const qCount = (curSec.questions?.length || 0) + 1;

    const newQ: FormQuestion = {
      id: `q-${Date.now()}-${qCount}`,
      code: `Q_${curSec.code}_${qCount}`,
      label: `Nuevo Grupo de Preguntas / Criterio ${qCount}`,
      card_template: {
        id: `ct-${Date.now()}-${qCount}`,
        code: `CT_${curSec.code}_${qCount}`,
        label: `Plantilla de Respuestas ${qCount}`,
        field_groups: [
          {
            id: `fg-${Date.now()}-${qCount}`,
            code: `FG_${qCount}`,
            label: 'Criterios de Verificación',
            fields: [
              {
                id: `f-${Date.now()}-1`,
                code: `CAMPO_${qCount}_01`,
                label: 'Enunciado de la pregunta de verificación...',
                field_type_id: 'ft-bool',
                field_type_code: 'boolean',
                is_required: true,
              },
            ],
          },
        ],
      },
    };

    const updatedSecs = [...sections];
    updatedSecs[activeSectionIndex].questions = [
      ...(updatedSecs[activeSectionIndex].questions || []),
      newQ,
    ];
    setSections(updatedSecs);
    setActiveQuestionIndex((updatedSecs[activeSectionIndex].questions?.length || 1) - 1);
  };

  // Remove Question
  const handleRemoveQuestion = (qIdx: number) => {
    const curSec = sections[activeSectionIndex];
    if (!curSec || !curSec.questions || curSec.questions.length <= 1) {
      alert('La dimensión debe tener al menos 1 pregunta o criterio.');
      return;
    }
    const updatedSecs = [...sections];
    updatedSecs[activeSectionIndex].questions = curSec.questions.filter((_, idx) => idx !== qIdx);
    setSections(updatedSecs);
    setActiveQuestionIndex(Math.max(0, qIdx - 1));
  };

  // Move Question Up/Down
  const handleMoveQuestion = (qIdx: number, direction: 'up' | 'down') => {
    const curSec = sections[activeSectionIndex];
    if (!curSec || !curSec.questions) return;
    if ((direction === 'up' && qIdx === 0) || (direction === 'down' && qIdx === curSec.questions.length - 1)) return;
    const targetIdx = direction === 'up' ? qIdx - 1 : qIdx + 1;
    const updatedSecs = [...sections];
    const questions = [...(updatedSecs[activeSectionIndex].questions || [])];
    const temp = questions[qIdx];
    questions[qIdx] = questions[targetIdx];
    questions[targetIdx] = temp;
    updatedSecs[activeSectionIndex].questions = questions;
    setSections(updatedSecs);
    setActiveQuestionIndex(targetIdx);
  };

  // Add Field to active question
  const handleAddField = (
    typeCode: 'boolean' | 'numeric' | 'text' | 'date' | 'singlechoice'
  ) => {
    const curSec = sections[activeSectionIndex];
    if (!curSec || !curSec.questions) return;
    const curQ = curSec.questions[activeQuestionIndex];
    if (!curQ || !curQ.card_template.field_groups[0]) return;

    const fCount = curQ.card_template.field_groups[0].fields.length + 1;

    let defaultChoices: FieldChoice[] | undefined = undefined;
    if (typeCode === 'singlechoice') {
      defaultChoices = [
        { id: `ch-${Date.now()}-1`, code: 'NIVEL_BASICO', label: 'Nivel Inicial / Básico (0-25%)', score_weight: 25 },
        { id: `ch-${Date.now()}-2`, code: 'NIVEL_INTERMEDIO', label: 'Nivel Intermedio / En Consolidación (26-70%)', score_weight: 70 },
        { id: `ch-${Date.now()}-3`, code: 'NIVEL_AVANZADO', label: 'Nivel Avanzado / Referente Distrital (71-100%)', score_weight: 100 },
      ];
    }

    const newField: FormField = {
      id: `f-${Date.now()}-${fCount}`,
      code: `VAR_${curQ.code}_${fCount}`,
      label: `Nuevo campo ${fCount}: Indique la evidencia o valor correspondiente`,
      field_type_id: `ft-${typeCode}`,
      field_type_code: typeCode,
      is_required: true,
      unit: typeCode === 'numeric' ? 'unidades' : undefined,
      min_value: typeCode === 'numeric' ? 0 : undefined,
      choices: defaultChoices,
    };

    const updatedSecs = [...sections];
    const sIdx = Math.min(Math.max(0, activeSectionIndex), Math.max(0, updatedSecs.length - 1));
    const qIdx = updatedSecs[sIdx]?.questions ? Math.min(Math.max(0, activeQuestionIndex), Math.max(0, updatedSecs[sIdx].questions.length - 1)) : 0;
    if (!updatedSecs[sIdx]?.questions?.[qIdx]) return;
    
    updatedSecs[sIdx].questions[qIdx].card_template.field_groups[0].fields.push(newField);
    setSections(updatedSecs);
  };

  // Remove Field
  const handleRemoveField = (fieldIdx: number) => {
    const sIdx = Math.min(Math.max(0, activeSectionIndex), Math.max(0, sections.length - 1));
    const curSec = sections[sIdx];
    if (!curSec || !curSec.questions) return;
    const qIdx = Math.min(Math.max(0, activeQuestionIndex), Math.max(0, curSec.questions.length - 1));
    const curQ = curSec.questions[qIdx];
    if (!curQ || !curQ.card_template.field_groups[0]) return;

    if (curQ.card_template.field_groups[0].fields.length <= 1) {
      alert('La pregunta debe tener al menos 1 campo.');
      return;
    }

    const updatedSecs = [...sections];
    updatedSecs[sIdx].questions![qIdx].card_template.field_groups[0].fields =
      curQ.card_template.field_groups[0].fields.filter((_, idx) => idx !== fieldIdx);
    setSections(updatedSecs);
  };

  // Update Field Properties
  const handleUpdateField = (fieldIdx: number, updates: Partial<FormField>) => {
    const sIdx = Math.min(Math.max(0, activeSectionIndex), Math.max(0, sections.length - 1));
    const updatedSecs = [...sections];
    if (!updatedSecs[sIdx]?.questions) return;
    const qIdx = Math.min(Math.max(0, activeQuestionIndex), Math.max(0, updatedSecs[sIdx].questions.length - 1));
    const target =
      updatedSecs[sIdx].questions[qIdx].card_template.field_groups[0].fields[fieldIdx];
    if (target) {
      updatedSecs[sIdx].questions[qIdx].card_template.field_groups[0].fields[fieldIdx] = {
        ...target,
        ...updates,
      };
      setSections(updatedSecs);
    }
  };

  // Add Choice to Single Choice Field
  const handleAddChoice = (fieldIdx: number) => {
    const sIdx = Math.min(Math.max(0, activeSectionIndex), Math.max(0, sections.length - 1));
    const updatedSecs = [...sections];
    if (!updatedSecs[sIdx]?.questions) return;
    const qIdx = Math.min(Math.max(0, activeQuestionIndex), Math.max(0, updatedSecs[sIdx].questions.length - 1));
    const field =
      updatedSecs[sIdx].questions[qIdx].card_template.field_groups[0].fields[fieldIdx];
    if (!field) return;
    const choices = field.choices || [];
    const newChoice: FieldChoice = {
      id: `ch-${Date.now()}-${choices.length + 1}`,
      code: `OPCION_${choices.length + 1}`,
      label: `Opción ${choices.length + 1}`,
      score_weight: 10,
    };
    field.choices = [...choices, newChoice];
    setSections(updatedSecs);
  };

  const handleRemoveChoice = (fieldIdx: number, choiceIdx: number) => {
    const sIdx = Math.min(Math.max(0, activeSectionIndex), Math.max(0, sections.length - 1));
    const updatedSecs = [...sections];
    if (!updatedSecs[sIdx]?.questions) return;
    const qIdx = Math.min(Math.max(0, activeQuestionIndex), Math.max(0, updatedSecs[sIdx].questions.length - 1));
    const field =
      updatedSecs[sIdx].questions[qIdx].card_template.field_groups[0].fields[fieldIdx];
    if (field?.choices && field.choices.length > 1) {
      field.choices = field.choices.filter((_, idx) => idx !== choiceIdx);
      setSections(updatedSecs);
    }
  };

  const handleUpdateChoice = (
    fieldIdx: number,
    choiceIdx: number,
    updates: Partial<FieldChoice>
  ) => {
    const sIdx = Math.min(Math.max(0, activeSectionIndex), Math.max(0, sections.length - 1));
    const updatedSecs = [...sections];
    if (!updatedSecs[sIdx]?.questions) return;
    const qIdx = Math.min(Math.max(0, activeQuestionIndex), Math.max(0, updatedSecs[sIdx].questions.length - 1));
    const field =
      updatedSecs[sIdx].questions[qIdx].card_template.field_groups[0].fields[fieldIdx];
    if (field?.choices && field.choices[choiceIdx]) {
      field.choices[choiceIdx] = { ...field.choices[choiceIdx], ...updates };
      setSections(updatedSecs);
    }
  };

  // Save Form
  const handleSave = async () => {
    if (!label.trim()) {
      setErrorMsg('El título del formulario es obligatorio.');
      return;
    }
    if (!code.trim()) {
      setErrorMsg('El código del formulario es obligatorio.');
      return;
    }

    setIsSaving(true);
    setErrorMsg(null);

    const compiledForm: IIPForm = {
      id: initialForm?.id || `form-iip-${Date.now()}`,
      code: code.trim().toUpperCase(),
      label: label.trim(),
      description: description.trim() || null,
      year: Number(year),
      version: version.trim() || '1.0',
      is_active: isActive,
      sections: sections.map((sec, sIdx) => ({
        ...sec,
        order_index: sIdx + 1,
      })),
    };

    try {
      await onSave(compiledForm);
      onClose();
    } catch (err: any) {
      setErrorMsg(err?.message || 'Error al guardar el formulario.');
    } finally {
      setIsSaving(false);
    }
  };

  const safeSectionIndex = Math.min(Math.max(0, activeSectionIndex), Math.max(0, sections.length - 1));
  const currentSection = sections[safeSectionIndex];
  const safeQuestionIndex = currentSection?.questions ? Math.min(Math.max(0, activeQuestionIndex), Math.max(0, currentSection.questions.length - 1)) : 0;
  const currentQuestion = currentSection?.questions?.[safeQuestionIndex];
  const currentFields = currentQuestion?.card_template?.field_groups?.[0]?.fields || [];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-3 sm:p-6 animate-in fade-in">
      <div className="bg-white w-full max-w-6xl rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Modal Top Header (LabCapital / Veeduría Distrital Theme) */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500 text-slate-950 flex items-center justify-center font-black shadow-md">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                  LabCapital • Veeduría Distrital
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                  {isEditing ? 'Modo Edición' : 'Diseñador de Cuestionarios IIP'}
                </span>
              </div>
              <h2 className="text-base sm:text-lg font-bold text-white leading-tight">
                {isEditing ? `Editar Formulario: ${label}` : 'Crear Nuevo Formulario de Diagnóstico IIP'}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPreviewMode(!isPreviewMode)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                isPreviewMode
                  ? 'bg-amber-500 text-slate-950 shadow-xs'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>{isPreviewMode ? 'Volver al Editor' : 'Vista Previa'}</span>
            </button>

            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="bg-rose-50 border-b border-rose-200 px-6 py-2.5 text-xs text-rose-800 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Modal Main Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
          {isPreviewMode ? (
            /* LIVE PREVIEW */
            <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
              <div className="border-b border-slate-200 pb-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-amber-600 uppercase tracking-wider">
                  <span>Vigencia {year}</span>
                  <span>•</span>
                  <span>Versión {version}</span>
                  <span>•</span>
                  <span className="font-mono text-slate-500">{code}</span>
                </div>
                <h3 className="text-xl font-bold text-slate-900 mt-1">{label}</h3>
                <p className="text-sm text-slate-600 mt-1">{description}</p>
              </div>

              <div className="space-y-6">
                {sections.map((sec, sIdx) => (
                  <div
                    key={sec.id}
                    className="p-5 rounded-2xl border border-slate-200 bg-slate-50 space-y-4"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-900 text-amber-400 flex items-center justify-center font-bold text-xs">
                        {sIdx + 1}
                      </div>
                      <div>
                        <h4 className="font-bold text-slate-900 text-sm">{sec.label}</h4>
                        <p className="text-xs text-slate-500">{sec.description}</p>
                      </div>
                    </div>

                    <div className="space-y-3 pl-4 sm:pl-11">
                      {sec.questions?.map((q) => (
                        <div
                          key={q.id}
                          className="p-4 bg-white rounded-xl border border-slate-200 space-y-3"
                        >
                          <div className="font-semibold text-xs text-slate-800">{q.label}</div>
                          <div className="space-y-2">
                            {q.card_template.field_groups[0]?.fields.map((f) => (
                              <div
                                key={f.id}
                                className="p-3 bg-slate-50/80 rounded-lg border border-slate-100 text-xs space-y-1"
                              >
                                <div className="font-medium text-slate-700 flex items-center justify-between">
                                  <span>{f.label}</span>
                                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 bg-slate-200 text-slate-600 rounded">
                                    {f.field_type_code}
                                  </span>
                                </div>
                                {f.help_text && (
                                  <p className="text-[11px] text-slate-400">{f.help_text}</p>
                                )}
                                {f.choices && (
                                  <div className="pt-1 flex flex-wrap gap-2">
                                    {f.choices.map((c) => (
                                      <span
                                        key={c.id}
                                        className="px-2 py-1 bg-white border border-slate-200 rounded text-[11px] text-slate-600"
                                      >
                                        {c.label} ({c.score_weight} pts)
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* EDITOR MODE */
            <div className="space-y-6">
              {/* General Form Info Card */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <Sliders className="w-4 h-4 text-amber-500" />
                    <span>1. Parámetros Generales del Formulario</span>
                  </h3>
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-700">
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={(e) => setIsActive(e.target.checked)}
                      className="rounded text-amber-600 focus:ring-amber-500 w-4 h-4"
                    />
                    <span>Formulario Activo para Diligenciamiento</span>
                  </label>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
                  <div className="sm:col-span-8">
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Título Oficial del Cuestionario <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={label}
                      onChange={(e) => setLabel(e.target.value)}
                      placeholder="Ej. Índice de Innovación Pública - Medición Anual Distrital 2026"
                      className="w-full text-xs font-semibold px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                    />
                  </div>

                  <div className="sm:col-span-4">
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Código Técnico <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={code}
                      onChange={(e) => setCode(e.target.value.toUpperCase())}
                      placeholder="IIP_2026_V1"
                      className="w-full text-xs font-mono font-bold px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                    />
                  </div>

                  <div className="sm:col-span-8">
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Descripción y Alcance Institucional
                    </label>
                    <input
                      type="text"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Instrumento de recolección para las entidades del Distrito Capital..."
                      className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs font-bold text-slate-700 mb-1">Año / Vigencia</label>
                    <input
                      type="number"
                      value={year}
                      onChange={(e) => setYear(Number(e.target.value))}
                      className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs font-bold text-slate-700 mb-1">Versión</label>
                    <input
                      type="text"
                      value={version}
                      onChange={(e) => setVersion(e.target.value)}
                      placeholder="1.0"
                      className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                    />
                  </div>
                </div>
              </div>

              {/* Hierarchical Builder Area (Sections & Questions) */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Column: Dimensions / Sections List */}
                <div className="lg:col-span-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                      <Layers className="w-4 h-4 text-amber-500" />
                      <span>Dimensiones ({sections.length})</span>
                    </h3>
                    <button
                      type="button"
                      onClick={handleAddSection}
                      className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 text-xs font-bold rounded-lg flex items-center gap-1 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Agregar Dimensión</span>
                    </button>
                  </div>

                  <div className="space-y-2">
                    {sections.map((sec, idx) => (
                      <div
                        key={sec.id}
                        onClick={() => {
                          setActiveSectionIndex(idx);
                          setActiveQuestionIndex(0);
                        }}
                        className={`p-3 rounded-xl border transition-all cursor-pointer text-xs ${
                          safeSectionIndex === idx
                            ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                            : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5 mb-1">
                              <span
                                className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                                  safeSectionIndex === idx ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-100 text-slate-600'
                                }`}
                              >
                                Dim {idx + 1}
                              </span>
                              <span className={`text-[10px] font-mono truncate ${safeSectionIndex === idx ? 'text-slate-300' : 'text-slate-400'}`}>
                                {sec.code}
                              </span>
                            </div>
                            <div className="font-semibold line-clamp-2">{sec.label}</div>
                            <span
                              className={`text-[11px] block mt-1.5 ${
                                safeSectionIndex === idx ? 'text-slate-400' : 'text-slate-400'
                              }`}
                            >
                              {sec.questions?.length || 0} {sec.questions?.length === 1 ? 'criterio' : 'criterios'}
                            </span>
                          </div>

                          <div className="flex items-center gap-0.5 shrink-0">
                            <button
                              type="button"
                              disabled={idx === 0}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleMoveSection(idx, 'up');
                              }}
                              className={`p-1 rounded transition-colors ${
                                idx === 0
                                  ? 'text-slate-300/30 cursor-not-allowed'
                                  : safeSectionIndex === idx
                                  ? 'text-slate-400 hover:text-white hover:bg-slate-800'
                                  : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'
                              }`}
                              title="Mover dimensión arriba"
                            >
                              <MoveUp className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              disabled={idx === sections.length - 1}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleMoveSection(idx, 'down');
                              }}
                              className={`p-1 rounded transition-colors ${
                                idx === sections.length - 1
                                  ? 'text-slate-300/30 cursor-not-allowed'
                                  : safeSectionIndex === idx
                                  ? 'text-slate-400 hover:text-white hover:bg-slate-800'
                                  : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'
                              }`}
                              title="Mover dimensión abajo"
                            >
                              <MoveDown className="w-3.5 h-3.5" />
                            </button>
                            {sections.length > 1 && (
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleRemoveSection(idx);
                                }}
                                className={`p-1 rounded transition-colors ${
                                  safeSectionIndex === idx
                                    ? 'text-slate-400 hover:text-rose-400 hover:bg-slate-800'
                                    : 'text-slate-400 hover:text-rose-600 hover:bg-rose-50'
                                }`}
                                title="Eliminar dimensión"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right Column: Questions & Fields Editor */}
                <div className="lg:col-span-8 space-y-4">
                  {currentSection ? (
                    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-5">
                      {/* Active Dimension Details */}
                      <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider">
                            Configuración de Dimensión {safeSectionIndex + 1} de {sections.length}
                          </span>
                          <span className="text-[11px] text-slate-500">
                            {currentSection.questions?.length || 0} criterios configurados
                          </span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
                          <div className="sm:col-span-8">
                            <label className="block text-[11px] font-bold text-slate-600 mb-0.5">
                              Nombre de la Dimensión
                            </label>
                            <input
                              type="text"
                              value={currentSection.label}
                              onChange={(e) => {
                                const updated = [...sections];
                                updated[safeSectionIndex].label = e.target.value;
                                setSections(updated);
                              }}
                              className="w-full text-xs font-semibold px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                            />
                          </div>

                          <div className="sm:col-span-4">
                            <label className="block text-[11px] font-bold text-slate-600 mb-0.5">
                              Código Dimensión
                            </label>
                            <input
                              type="text"
                              value={currentSection.code}
                              onChange={(e) => {
                                const updated = [...sections];
                                updated[safeSectionIndex].code = e.target.value.toUpperCase();
                                setSections(updated);
                              }}
                              className="w-full text-xs font-mono font-bold px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                            />
                          </div>

                          <div className="sm:col-span-8">
                            <label className="block text-[11px] font-bold text-slate-600 mb-0.5">
                              Descripción del Criterio
                            </label>
                            <input
                              type="text"
                              value={currentSection.description || ''}
                              onChange={(e) => {
                                const updated = [...sections];
                                updated[safeSectionIndex].description = e.target.value;
                                setSections(updated);
                              }}
                              className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                            />
                          </div>

                          <div className="sm:col-span-4">
                            <label className="block text-[11px] font-bold text-slate-600 mb-0.5">
                              Ícono Representativo
                            </label>
                            <select
                              value={currentSection.icon_name || 'Building2'}
                              onChange={(e) => {
                                const updated = [...sections];
                                updated[safeSectionIndex].icon_name = e.target.value;
                                setSections(updated);
                              }}
                              className="w-full text-xs font-semibold px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                            >
                              {ICON_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>
                      </div>

                      {/* Question Tabs within this Dimension */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                          <div className="flex items-center gap-2 overflow-x-auto">
                            {currentSection.questions?.map((q, qIdx) => (
                              <div key={q.id} className="flex items-center">
                                <button
                                  type="button"
                                  onClick={() => setActiveQuestionIndex(qIdx)}
                                  className={`px-3 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
                                    safeQuestionIndex === qIdx
                                      ? 'bg-slate-900 text-white'
                                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                  }`}
                                >
                                  Criterio {qIdx + 1}
                                </button>
                              </div>
                            ))}
                          </div>

                          <button
                            type="button"
                            onClick={handleAddQuestion}
                            className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg flex items-center gap-1 transition-colors whitespace-nowrap shrink-0"
                          >
                            <Plus className="w-3.5 h-3.5" />
                            <span>Añadir Criterio</span>
                          </button>
                        </div>

                        {currentQuestion && (
                          <div className="space-y-4 pt-1">
                            {/* Question Title, Code & Actions */}
                            <div className="flex items-center justify-between">
                              <span className="text-[11px] font-bold text-indigo-700 uppercase tracking-wider">
                                Criterio / Pregunta {safeQuestionIndex + 1} de {currentSection.questions?.length || 1}
                              </span>
                              <div className="flex items-center gap-1">
                                <button
                                  type="button"
                                  disabled={safeQuestionIndex === 0}
                                  onClick={() => handleMoveQuestion(safeQuestionIndex, 'up')}
                                  className="px-2 py-0.5 text-xs text-slate-600 hover:bg-slate-100 rounded disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1"
                                  title="Mover criterio arriba"
                                >
                                  <MoveUp className="w-3.5 h-3.5" />
                                  <span>Subir</span>
                                </button>
                                <button
                                  type="button"
                                  disabled={safeQuestionIndex === (currentSection.questions?.length || 1) - 1}
                                  onClick={() => handleMoveQuestion(safeQuestionIndex, 'down')}
                                  className="px-2 py-0.5 text-xs text-slate-600 hover:bg-slate-100 rounded disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1"
                                  title="Mover criterio abajo"
                                >
                                  <MoveDown className="w-3.5 h-3.5" />
                                  <span>Bajar</span>
                                </button>
                                {(currentSection.questions?.length || 0) > 1 && (
                                  <button
                                    type="button"
                                    onClick={() => handleRemoveQuestion(safeQuestionIndex)}
                                    className="px-2 py-0.5 text-xs text-rose-600 hover:bg-rose-50 rounded flex items-center gap-1"
                                    title="Eliminar criterio"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                    <span>Eliminar</span>
                                  </button>
                                )}
                              </div>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
                              <div className="sm:col-span-8">
                                <label className="block text-[11px] font-bold text-slate-600 mb-0.5">
                                  Título del Grupo / Pregunta
                                </label>
                                <input
                                  type="text"
                                  value={currentQuestion.label}
                                  onChange={(e) => {
                                    const updated = [...sections];
                                    updated[safeSectionIndex].questions![safeQuestionIndex].label =
                                      e.target.value;
                                    setSections(updated);
                                  }}
                                  className="w-full text-xs font-semibold px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                                />
                              </div>

                              <div className="sm:col-span-4">
                                <label className="block text-[11px] font-bold text-slate-600 mb-0.5">
                                  Código
                                </label>
                                <input
                                  type="text"
                                  value={currentQuestion.code}
                                  onChange={(e) => {
                                    const updated = [...sections];
                                    updated[safeSectionIndex].questions![safeQuestionIndex].code =
                                      e.target.value.toUpperCase();
                                    setSections(updated);
                                  }}
                                  className="w-full text-xs font-mono font-bold px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                                />
                              </div>
                            </div>

                            {/* Fields List of this Question */}
                            <div className="space-y-3">
                              <div className="flex items-center justify-between pt-2">
                                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                                  Campos de Respuesta ({currentFields.length})
                                </h4>

                                <div className="flex items-center gap-1.5">
                                  <span className="text-[11px] text-slate-400 font-medium mr-1">
                                    + Agregar campo:
                                  </span>
                                  <button
                                    type="button"
                                    onClick={() => handleAddField('boolean')}
                                    className="px-2 py-1 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 rounded text-[11px] font-semibold"
                                  >
                                    Sí / No
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleAddField('numeric')}
                                    className="px-2 py-1 bg-sky-50 hover:bg-sky-100 text-sky-900 border border-sky-200 rounded text-[11px] font-semibold"
                                  >
                                    Numérico
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleAddField('singlechoice')}
                                    className="px-2 py-1 bg-purple-50 hover:bg-purple-100 text-purple-900 border border-purple-200 rounded text-[11px] font-semibold"
                                  >
                                    Selección Única
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleAddField('text')}
                                    className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 rounded text-[11px] font-semibold"
                                  >
                                    Texto
                                  </button>
                                </div>
                              </div>

                              <div className="space-y-3">
                                {currentFields.map((field, fIdx) => (
                                  <div
                                    key={field.id}
                                    className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3"
                                  >
                                    <div className="flex items-start justify-between gap-2">
                                      <div className="flex items-center gap-2">
                                        <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-bold text-[10px]">
                                          {fIdx + 1}
                                        </span>
                                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 bg-slate-900 text-amber-400 font-bold rounded">
                                          {field.field_type_code}
                                        </span>
                                        {field.is_required && (
                                          <span className="text-[10px] font-semibold text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                                            Obligatorio
                                          </span>
                                        )}
                                      </div>

                                      {currentFields.length > 1 && (
                                        <button
                                          type="button"
                                          onClick={() => handleRemoveField(fIdx)}
                                          className="text-slate-400 hover:text-rose-600 p-1"
                                          title="Eliminar campo"
                                        >
                                          <Trash2 className="w-3.5 h-3.5" />
                                        </button>
                                      )}
                                    </div>

                                    {/* Field Label & Code */}
                                    <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
                                      <div className="sm:col-span-8">
                                        <label className="block text-[10px] font-bold text-slate-500 mb-0.5">
                                          Pregunta o Enunciado del Campo
                                        </label>
                                        <input
                                          type="text"
                                          value={field.label}
                                          onChange={(e) =>
                                            handleUpdateField(fIdx, { label: e.target.value })
                                          }
                                          className="w-full text-xs font-semibold px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                                        />
                                      </div>

                                      <div className="sm:col-span-4">
                                        <label className="block text-[10px] font-bold text-slate-500 mb-0.5">
                                          Código de Variable
                                        </label>
                                        <input
                                          type="text"
                                          value={field.code}
                                          onChange={(e) =>
                                            handleUpdateField(fIdx, {
                                              code: e.target.value.toUpperCase(),
                                            })
                                          }
                                          className="w-full text-xs font-mono px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                                        />
                                      </div>

                                      <div className="sm:col-span-8">
                                        <label className="block text-[10px] font-bold text-slate-500 mb-0.5">
                                          Texto de Ayuda / Criterio de Evidencia
                                        </label>
                                        <input
                                          type="text"
                                          value={field.help_text || ''}
                                          onChange={(e) =>
                                            handleUpdateField(fIdx, { help_text: e.target.value })
                                          }
                                          placeholder="Ej. Ingrese el número de resolución o enlace institucional..."
                                          className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                                        />
                                      </div>

                                      {field.field_type_code === 'numeric' && (
                                        <div className="sm:col-span-4">
                                          <label className="block text-[10px] font-bold text-slate-500 mb-0.5">
                                            Unidad de Medida
                                          </label>
                                          <input
                                            type="text"
                                            value={field.unit || ''}
                                            onChange={(e) =>
                                              handleUpdateField(fIdx, { unit: e.target.value })
                                            }
                                            placeholder="%, personas, millones COP"
                                            className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                                          />
                                        </div>
                                      )}
                                    </div>

                                    {/* Choice Options for singlechoice */}
                                    {field.field_type_code === 'singlechoice' && (
                                      <div className="mt-2 pt-2 border-t border-slate-200/80 space-y-2">
                                        <div className="flex items-center justify-between">
                                          <span className="text-[11px] font-bold text-purple-900">
                                            Opciones de Selección y Ponderación de Puntaje
                                          </span>
                                          <button
                                            type="button"
                                            onClick={() => handleAddChoice(fIdx)}
                                            className="px-2 py-0.5 bg-purple-100 hover:bg-purple-200 text-purple-800 text-[10px] font-bold rounded"
                                          >
                                            + Opción
                                          </button>
                                        </div>

                                        <div className="space-y-1.5">
                                          {field.choices?.map((ch, cIdx) => (
                                            <div
                                              key={ch.id}
                                              className="flex items-center gap-2 text-xs bg-white p-2 rounded-lg border border-slate-200"
                                            >
                                              <input
                                                type="text"
                                                value={ch.label}
                                                onChange={(e) =>
                                                  handleUpdateChoice(fIdx, cIdx, {
                                                    label: e.target.value,
                                                  })
                                                }
                                                placeholder="Texto de la opción"
                                                className="flex-1 text-xs px-2 py-1 border border-slate-200 rounded"
                                              />
                                              <div className="flex items-center gap-1">
                                                <span className="text-[10px] text-slate-500 font-medium">
                                                  Pts:
                                                </span>
                                                <input
                                                  type="number"
                                                  value={ch.score_weight ?? 0}
                                                  onChange={(e) =>
                                                    handleUpdateChoice(fIdx, cIdx, {
                                                      score_weight: Number(e.target.value),
                                                    })
                                                  }
                                                  className="w-16 text-xs px-2 py-1 border border-slate-200 rounded text-right font-bold"
                                                />
                                              </div>
                                              {field.choices && field.choices.length > 1 && (
                                                <button
                                                  type="button"
                                                  onClick={() => handleRemoveChoice(fIdx, cIdx)}
                                                  className="text-slate-400 hover:text-rose-600 p-1"
                                                >
                                                  <Trash2 className="w-3 h-3" />
                                                </button>
                                              )}
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Bottom Footer Actions */}
        <div className="bg-slate-100 px-6 py-4 flex items-center justify-between border-t border-slate-200">
          <div className="text-xs text-slate-500">
            {sections.length} Dimensiones •{' '}
            {sections.reduce((acc, s) => acc + (s.questions?.length || 0), 0)} Criterios configurados
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-white hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl border border-slate-300 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="px-5 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {isSaving ? (
                <div className="w-3.5 h-3.5 border-2 border-slate-950/30 border-t-slate-950 rounded-full animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4" />
              )}
              <span>{isEditing ? 'Actualizar Formulario' : 'Guardar Formulario IIP'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
