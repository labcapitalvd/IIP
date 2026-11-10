/**
 * Types definition for Índice de Innovación Pública (IIP)
 */

export type UserRole = 'admin' | 'entity';

export type PlatformHeader = 'web' | 'mobile';

export interface AuthTokens {
  access_token: string;
  refresh_token: string | null;
  token_type: 'bearer';
}

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  password?: string;
  role: UserRole;
  actor_id?: string; // If role is 'entity', linked to specific Actor
  actor_label?: string;
  actor_segment_label?: string;
  is_active?: boolean;
  approval_status?: 'pending' | 'approved' | 'rejected';
  created_at?: string;
  phone?: string;
  contact_person?: string;
}

export type AssignmentStatus = 'pending' | 'in_progress' | 'submitted' | 'reviewed';

export interface FormAssignment {
  id: string;
  form_id: string;
  form_code: string;
  form_title: string;
  form_year: number;
  user_id: string;
  user_name: string;
  user_email: string;
  actor_id: string;
  actor_label: string;
  actor_segment_label?: string;
  assigned_at: string;
  due_date: string;
  status: AssignmentStatus;
  completion_percentage: number;
  score?: number;
  submission_id?: string;
  radicado_number?: string;
  submitted_at?: string;
  notes?: string;
}

/** Formulario asignado al usuario autenticado (GET /public/forms/assignments/me). */
export interface EntityAssignment {
  id: string;
  form_id: string;
  form_code: string;
  form_label: string;
  form_description?: string;
  actor_id?: string;
  actor_label?: string;
  assigned_at: string;
  due_date?: string;
  notes?: string;
  status: 'pending' | 'in_progress' | 'submitted';
  completion_percentage: number;
  submission_id?: string;
  /** Componentes que la entidad eligió responder (null/ausente = aún no ha elegido). */
  selected_component_ids?: string[] | null;
  /** Última solicitud de modificación de la entidad para este formulario ya enviado. */
  reopen_status?: ReopenStatus | null;
  reopen_note?: string | null;
}

export type ReopenStatus = 'pending' | 'approved' | 'rejected';

/** Solicitud de una entidad para modificar un formulario ya enviado (GET /public/submissions/reopen-requests). */
export interface ReopenRequest {
  id: string;
  form_id: string;
  form_code: string;
  form_label: string;
  actor_id: string;
  actor_label: string;
  requested_by_name?: string;
  reason: string;
  status: ReopenStatus;
  requested_at: string;
  resolved_at?: string;
  resolution_note?: string;
}

export interface CreateEntityUserPayload {
  username: string;
  email: string;
  password?: string;
  actor_id: string;
  actor_label?: string;
  contact_person?: string;
  phone?: string;
  assign_form_id?: string;
  due_date?: string;
  is_active?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string | null;
  message: string;
  token_type: 'bearer';
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  actor_id?: string;
  actor_label?: string;
  contact_person?: string;
  phone?: string;
}

// POST /public/auth/register-admin — requires the server's ADMIN_REGISTRATION_KEY.
export interface RegisterAdminPayload {
  username: string;
  email: string;
  password: string;
  registration_key: string;
  contact_person?: string;
}

// GET /public/auth/me — the backend's own view of "who is logged in",
// resolved from the DB every time. This replaces any locally cached profile.
export interface MeActorLink {
  actor_id: string;
  actor_label: string;
  resource_role: string | null;
}

export interface MeResponse {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  tier: string | null;
  system_roles: string[];
  actor_links: MeActorLink[];
  name: string | null;
  phone: string | null;
}

export interface ApiErrorResponse {
  status: 'error';
  code: string;
  message: string;
  detail?: any;
}

// Actor & Segment Types
export interface ActorSegment {
  id: string;
  label: string;
  description: string | null;
  actors?: Actor[];
}

export interface Actor {
  id: string;
  label: string;
  description: string | null;
  mission: string | null;
  vision: string | null;
  actor_segment_id?: string | null;
  actor_segment?: {
    id: string;
    label: string;
    description: string | null;
  } | null;
  contact_email?: string;
  contact_phone?: string;
  head_of_entity?: string;
}

export interface ActorCreatePayload {
  id?: string | null;
  label: string;
  description: string | null;
  mission: string | null;
  vision: string | null;
  actor_segment_id: string | null;
}

export interface ActorSegmentCreatePayload {
  id?: string | null;
  label: string;
  description: string | null;
}

// Form Hierarchy Types (as defined in Core Service POST /forms)
export type FieldTypeCode = 'boolean' | 'text' | 'numeric' | 'date' | 'singlechoice' | 'single_choice' | 'multichoice' | 'multi_choice' | 'file';

export interface FieldChoice {
  id: string;
  code: string;
  label: string;
  score_weight?: number;
}

export interface FormField {
  id: string;
  code: string;
  label: string;
  description?: string | null;
  field_type_id: string;
  field_type_code: 'boolean' | 'text' | 'numeric' | 'date' | 'singlechoice' | 'multichoice' | 'file';
  is_required: boolean;
  placeholder?: string;
  help_text?: string;
  unit?: string;
  /** Campos `file`: códigos de tipos de archivo permitidos y tamaño máximo en bytes. */
  allowed_file_types?: string[];
  max_file_size?: number;
  min_value?: number;
  max_value?: number;
  choices?: FieldChoice[];
}

export interface FieldGroup {
  id: string;
  code: string;
  label: string;
  description?: string | null;
  fields: FormField[];
}

export interface CardTemplate {
  id: string;
  code: string;
  label: string;
  description?: string | null;
  is_repeatable?: boolean;
  min_entries?: number;
  max_entries?: number;
  field_groups: FieldGroup[];
}

/**
 * Tipo de pregunta en el diseñador:
 * - text / numeric / single_choice / multi_choice / boolean: pregunta simple (un campo).
 * - loop: pregunta bucle (tarjetas repetibles). Se habilita según la respuesta Sí/No
 *   de otra pregunta del mismo indicador (`depends_on`).
 */
export type QuestionKind = 'text' | 'numeric' | 'single_choice' | 'multi_choice' | 'boolean' | 'file' | 'loop';

export interface QuestionDependency {
  /** id de la pregunta Sí/No de la que depende (mismo indicador). */
  question_id: string;
  /** Valor de esa pregunta que habilita el bucle (Sí = true). */
  value: boolean;
}

export interface FormQuestion {
  id: string;
  code: string;
  label: string;
  description?: string | null;
  help_text?: string;
  order_index?: number;
  question_kind?: QuestionKind;
  is_required?: boolean;
  depends_on?: QuestionDependency | null;
  /** Peso en la calificación manual (puntos sobre 100 en todo el formulario). */
  weight?: number;
  /** Guía para el calificador: qué verificar para puntuar esta pregunta. */
  grading_guide?: string;
  /**
   * Solo preguntas bucle: id de otra pregunta bucle (de cualquier componente) de cuyas tarjetas
   * cuelgan las de esta. Cada tarjeta se refiere a una tarjeta de la pregunta origen.
   */
  source_question_id?: string | null;
  card_template: CardTemplate;
}

export interface FormSection {
  id: string;
  code: string;
  label: string;
  description?: string | null;
  help_text?: string;
  order_index: number;
  icon_name?: string;
  /**
   * Jerarquía: Componente (raíz) → Variable → Indicador → Preguntas.
   * `children` son las Variables de un Componente o los Indicadores de una Variable;
   * solo los Indicadores tienen `questions`.
   */
  children?: FormSection[];
  questions?: FormQuestion[];
}

export interface IIPForm {
  id: string;
  code: string;
  label: string;
  description: string | null;
  year: number;
  version: string;
  is_active: boolean;
  sections: FormSection[];
  /**
   * true si el formulario viene del backend (su `id` es el UUID del servidor).
   * false = borrador que solo existe en este navegador hasta su primer guardado.
   */
  is_synced_to_backend?: boolean;
  /** Última actualización confirmada por el backend (ISO 8601). */
  updated_at?: string | null;
}

export interface FileTypeInfo {
  code: string;
  label: string;
  extension: string;
  mime_type: string;
  category: string;
  max_size: number;
}

export interface FormStatus {
  id: string;
  code: string;
  label: string;
  updated_at: string;
  has_submissions: boolean;
  /** Fecha de cierre de la edición: con ella la estructura ya no se puede modificar. */
  edition_closed_at?: string | null;
}

// GET /public/forms/historical — formulario con su estado de edición y datos históricos cargados.
export interface HistoricalForm {
  id: string;
  code: string;
  label: string;
  year?: number | null;
  is_active: boolean;
  edition_closed_at?: string | null;
  submission_count: number;
  result_count: number;
}

// GET /public/forms/historical/records — una fila por entidad × formulario con respuestas y/o resultados.
export interface MonitorRecord {
  form_id: string;
  form_code: string;
  form_label: string;
  form_year?: number | null;
  actor_id: string;
  actor_label: string;
  actor_segment_label?: string | null;
  /** Radicado de la entidad; ausente si solo hay resultados cargados. */
  submission_id?: string | null;
  status?: string | null;
  updated_at?: string | null;
  answer_count: number;
  card_count: number;
  has_results: boolean;
  total?: number | null;
}

// GET /public/forms/{form}/historical/results/{actor} — resultado estadístico cargado.
export interface EntityResults {
  has_results: boolean;
  total?: number | null;
  sections: Array<{ section_id: string; score?: number | null }>;
  updated_at?: string | null;
}

export interface HistoricalIssue {
  sheet: string;
  row?: number | null;
  column?: string | null;
  message: string;
}

export interface HistoricalReport {
  dry_run: boolean;
  committed: boolean;
  errors: HistoricalIssue[];
  warnings: HistoricalIssue[];
  summary: Record<string, number>;
}

// GET /public/forms — una fila por formulario guardado en el backend.
export interface FormSummary extends FormStatus {
  description: string | null;
  year: number | null;
  version: string | null;
  is_active: boolean;
}

// GET /public/forms/{form_id} — mismo árbol que el cuerpo de POST /forms, con ids.
export interface FieldChoiceTree {
  id: string;
  code: string;
  label: string;
  description: string | null;
  display_order: number;
}

export interface FieldTree {
  id: string;
  code: string;
  label: string;
  description: string | null;
  required: boolean;
  field_type_code: string;
  display_order: number;
  allowed_file_type_codes: string[];
  max_file_size: number | null;
  field_choices: FieldChoiceTree[];
}

export interface QuestionTree {
  id: string;
  code: string;
  label: string;
  description: string | null;
  helper: string | null;
  required: boolean;
  is_loop: boolean;
  display_order: number;
  weight?: number;
  grading_guide?: string | null;
  source_question_id?: string | null;
  depends_on: { question_id: string; expected_value: boolean } | null;
  card_template: {
    id: string;
    code: string;
    label: string;
    description: string | null;
    field_groups: {
      id: string;
      code: string;
      label: string;
      description: string | null;
      display_order: number;
      fields: FieldTree[];
    }[];
  } | null;
}

export interface SectionTree {
  id: string;
  code: string;
  label: string;
  description: string | null;
  helper: string | null;
  display_order: number;
  section_type_code: string | null;
  icon: string | null;
  questions: QuestionTree[];
  children: SectionTree[];
}

export interface FormTree extends FormSummary {
  sections: SectionTree[];
}

// Submission Payload Types (matching POST /submissions/forms/{form_id})
export interface BooleanAnswer {
  type: 'boolean';
  field_id: string;
  value: boolean;
}

export interface TextAnswer {
  type: 'text';
  field_id: string;
  value: string;
}

export interface NumericAnswer {
  type: 'numeric';
  field_id: string;
  value: number;
}

export interface DateAnswer {
  type: 'date';
  field_id: string;
  value: string; // YYYY-MM-DD
}

export interface SingleChoiceAnswer {
  type: 'single_choice';
  field_id: string;
  value: string; // UUID of chosen field_choice
}

export interface MultiChoiceAnswer {
  type: 'multi_choice';
  field_id: string;
  value: string[]; // UUIDs of the checked field_choices
}

export interface FileAnswer {
  type: 'file';
  field_id: string;
  value: string | null; // UUID of an already uploaded file
}

export interface CardEntryAnswer {
  type: 'card_entry';
  field_id?: string;
  question_id: string;
  card_template_id: string;
  title: string;
  card_index: number;
  /** Identificador temporal de la tarjeta dentro del envío (para que otras cuelguen de ella). */
  ref?: string;
  /** `ref` de la tarjeta (de la pregunta origen) de la que cuelga esta. */
  parent_ref?: string;
  answers: SubmissionValueAnswer[];
}

export type SubmissionValueAnswer =
  | BooleanAnswer
  | TextAnswer
  | NumericAnswer
  | DateAnswer
  | SingleChoiceAnswer
  | MultiChoiceAnswer
  | FileAnswer;

export type SubmissionItem =
  | SubmissionValueAnswer
  | CardEntryAnswer;

export interface EntitySubmission {
  id: string;
  form_id: string;
  form_code: string;
  form_title: string;
  actor_id: string;
  actor_label: string;
  actor_segment_label?: string;
  /** El backend no guarda qué usuario radicó, solo la entidad. */
  submitted_by?: string;
  submitted_at: string;
  status: 'draft' | 'submitted' | 'approved' | 'rejected';
  /** Código del estado en el backend (reference.submission_status_types). */
  status_code?: string;
  /** Aún no existe calificación en el backend; queda indefinido hasta que exista. */
  score?: number;
  answer_count?: number;
  card_count?: number;
  /** Etiquetas y valores legibles por campo (vienen del detalle del servidor). */
  field_labels?: Record<string, string>;
  display_values?: Record<string, string>;
  /** true cuando raw_answers / card_entries ya se cargaron del servidor. */
  detail_loaded?: boolean;
  completion_percentage: number;
  payload: SubmissionItem[];
  raw_answers: Record<string, any>;
  card_entries?: Record<
    string,
    Array<{
      id: string;
      title: string;
      answers: Record<string, any>;
      display?: Record<string, string>;
      /** Tarjeta de la pregunta origen de la que cuelga y su nombre (referencia). */
      parent_id?: string | null;
      parent_title?: string | null;
    }>
  >;
}

// System configuration and logs
export interface ApiConfig {
  authBaseUrl: string;
  coreBaseUrl: string;
  platform: PlatformHeader;
  saveTokensInStorage: boolean;
}

export interface HttpLog {
  id: string;
  timestamp: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  url: string;
  headers: Record<string, string>;
  body?: any;
  status: number;
  response: any;
  durationMs: number;
}
