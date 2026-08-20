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
  field_type_code: 'boolean' | 'text' | 'numeric' | 'date' | 'singlechoice';
  is_required: boolean;
  placeholder?: string;
  help_text?: string;
  unit?: string;
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

export interface FormQuestion {
  id: string;
  code: string;
  label: string;
  description?: string | null;
  order_index?: number;
  card_template: CardTemplate;
}

export interface FormSection {
  id: string;
  code: string;
  label: string;
  description?: string | null;
  order_index: number;
  icon_name?: string;
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
  type: 'singlechoice';
  field_id: string;
  value: string; // UUID of chosen field_choice
}

export interface CardEntryAnswer {
  type: 'card_entry';
  field_id?: string;
  question_id: string;
  card_template_id: string;
  title: string;
  card_index: number;
  answers: SubmissionValueAnswer[];
}

export type SubmissionValueAnswer =
  | BooleanAnswer
  | TextAnswer
  | NumericAnswer
  | DateAnswer
  | SingleChoiceAnswer;

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
  submitted_by: string;
  submitted_at: string;
  status: 'draft' | 'submitted' | 'approved' | 'rejected';
  score?: number;
  completion_percentage: number;
  payload: SubmissionItem[];
  raw_answers: Record<string, any>;
  card_entries?: Record<string, Array<{ id: string; title: string; answers: Record<string, any> }>>;
}

// System configuration and logs
export interface ApiConfig {
  authBaseUrl: string;
  coreBaseUrl: string;
  platform: PlatformHeader;
  useRealBackend: boolean;
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
  mode: 'real' | 'mock';
}
