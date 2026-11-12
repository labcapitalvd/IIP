import { apiClient } from './apiClient';
import {
  Actor,
  ActorCreatePayload,
  ActorSegment,
  ActorSegmentCreatePayload,
  EntityAssignment,
  ReopenRequest,
  ReopenStatus,
  FormAssignment,
  EntitySubmission,
  FileTypeInfo,
  FormStatus,
  FormSummary,
  FormTree,
  EntityResults,
  HistoricalForm,
  MonitorRecord,
  HistoricalReport,
  IIPForm,
  SubmissionItem,
} from '../types';
import { fromFormTree, toCreateFormRequest } from '../utils/formTree';

interface SubmissionSummaryApi {
  id: string;
  form_id: string;
  form_code: string;
  form_label: string;
  actor_id: string;
  actor_label: string;
  actor_segment_label?: string;
  status: string;
  updated_at: string;
  answer_count: number;
  card_count: number;
}

interface AnswerApi {
  field_id: string;
  field_label: string;
  value?: unknown;
  display: string;
}

interface SubmissionDetailApi extends SubmissionSummaryApi {
  answers: AnswerApi[];
  cards: Array<{
    id: string;
    question_id: string;
    title: string;
    card_index: number;
    parent_id?: string | null;
    parent_title?: string | null;
    answers: AnswerApi[];
  }>;
}

const mapSubmissionSummary = (s: SubmissionSummaryApi): EntitySubmission => ({
  id: s.id,
  form_id: s.form_id,
  form_code: s.form_code,
  form_title: s.form_label,
  actor_id: s.actor_id,
  actor_label: s.actor_label,
  actor_segment_label: s.actor_segment_label,
  submitted_at: s.updated_at,
  status:
    s.status === 'draft'
      ? 'draft'
      : s.status === 'approved' || s.status === 'rejected'
        ? s.status
        : 'submitted',
  status_code: s.status,
  completion_percentage: s.status === 'draft' ? 50 : 100,
  answer_count: s.answer_count,
  card_count: s.card_count,
  payload: [],
  raw_answers: {},
});

const mapSubmissionDetail = (d: SubmissionDetailApi): EntitySubmission => {
  const field_labels: Record<string, string> = {};
  const display_values: Record<string, string> = {};
  const raw_answers: Record<string, any> = {};
  d.answers.forEach((a) => {
    field_labels[a.field_id] = a.field_label;
    display_values[a.field_id] = a.display;
    raw_answers[a.field_id] = a.value;
  });
  const card_entries: NonNullable<EntitySubmission['card_entries']> = {};
  d.cards.forEach((c) => {
    const answers: Record<string, any> = {};
    const display: Record<string, string> = {};
    c.answers.forEach((a) => {
      field_labels[a.field_id] = a.field_label;
      answers[a.field_id] = a.value;
      display[a.field_id] = a.display;
    });
    (card_entries[c.question_id] ??= []).push({
      id: c.id,
      title: c.title,
      answers,
      display,
      parent_id: c.parent_id ?? null,
      parent_title: c.parent_title ?? null,
    });
  });
  return {
    ...mapSubmissionSummary(d),
    raw_answers,
    card_entries,
    field_labels,
    display_values,
    detail_loaded: true,
  };
};

interface AdminAssignmentItem {
  id: string;
  form_id: string;
  form_code: string;
  form_label: string;
  form_year?: number;
  user_id: string;
  user_name: string;
  user_email: string;
  actor_id?: string;
  actor_label?: string;
  actor_segment_label?: string;
  assigned_at: string;
  due_date?: string;
  notes?: string;
  status: FormAssignment['status'];
  completion_percentage: number;
  submission_id?: string;
}

export const coreService = {
  // --- ASIGNACIONES (/public/forms/assignments) ---

  /**
   * GET /public/forms/assignments/me
   * Formularios asignados al usuario autenticado, con el avance de su entidad.
   */
  async getMyAssignments(): Promise<EntityAssignment[]> {
    const { data } = await apiClient.request<EntityAssignment[]>('core', '/public/forms/assignments/me', {
      method: 'GET',
      requiresAuth: true,
    });
    return data;
  },

  /** PUT /public/forms/assignments/{id}/components — la entidad elige los componentes que responderá. */
  async selectAssignmentComponents(assignmentId: string, componentIds: string[]): Promise<void> {
    await apiClient.request('core', `/public/forms/assignments/${assignmentId}/components`, {
      method: 'PUT',
      body: { component_ids: componentIds },
      requiresAuth: true,
    });
  },

  /** POST /public/submissions/forms/{formId}/reopen-requests — la entidad pide modificar un envío. */
  async requestReopen(formId: string, reason: string): Promise<void> {
    await apiClient.request('core', `/public/submissions/forms/${formId}/reopen-requests`, {
      method: 'POST',
      body: { reason },
      requiresAuth: true,
    });
  },

  /** GET /public/submissions/reopen-requests — solicitudes de modificación (solo admin). */
  async listReopenRequests(status?: ReopenStatus): Promise<ReopenRequest[]> {
    const { data } = await apiClient.request<ReopenRequest[]>(
      'core',
      `/public/submissions/reopen-requests${status ? `?status=${status}` : ''}`,
      { method: 'GET', requiresAuth: true }
    );
    return data;
  },

  /** POST /public/submissions/reopen-requests/{id}/resolution — aprobar (vuelve a borrador) o rechazar. */
  async resolveReopenRequest(id: string, approve: boolean, note?: string): Promise<void> {
    await apiClient.request('core', `/public/submissions/reopen-requests/${id}/resolution`, {
      method: 'POST',
      body: { approve, note: note || null },
      requiresAuth: true,
    });
  },

  /** GET /public/forms/assignments — todas las asignaciones con su avance (solo admin). */
  async listAssignments(): Promise<FormAssignment[]> {
    const { data } = await apiClient.request<AdminAssignmentItem[]>('core', '/public/forms/assignments', {
      method: 'GET',
      requiresAuth: true,
    });
    return data.map((a) => ({
      id: a.id,
      form_id: a.form_id,
      form_code: a.form_code,
      form_title: a.form_label,
      form_year: a.form_year ?? 0,
      user_id: a.user_id,
      user_name: a.user_name,
      user_email: a.user_email,
      actor_id: a.actor_id ?? '',
      actor_label: a.actor_label ?? '',
      actor_segment_label: a.actor_segment_label,
      assigned_at: a.assigned_at,
      due_date: a.due_date ?? '',
      status: a.status,
      completion_percentage: a.completion_percentage,
      submission_id: a.submission_id,
      notes: a.notes,
    }));
  },

  /** POST /public/forms/assignments — asigna (o actualiza fecha/notas de) un formulario a un usuario. */
  async assignForm(payload: {
    user_id: string;
    form_id: string;
    due_date?: string | null;
    notes?: string;
  }): Promise<void> {
    await apiClient.request('core', '/public/forms/assignments', {
      method: 'POST',
      body: payload,
      requiresAuth: true,
    });
  },

  /** DELETE /public/forms/assignments/{id} — revoca la asignación (solo admin). */
  async deleteAssignment(id: string): Promise<void> {
    await apiClient.request('core', `/public/forms/assignments/${id}`, {
      method: 'DELETE',
      requiresAuth: true,
    });
  },

  // --- ACTORES (/public/actors) ---

  /**
   * GET /public/actors/all
   */
  async getActors(): Promise<Actor[]> {
    const { data } = await apiClient.request<Actor[]>('core', '/public/actors/all', {
      method: 'GET',
      requiresAuth: true,
    });
    return data;
  },

  /**
   * GET /public/actors/{actor_id}
   */
  async getActorById(actorId: string): Promise<Actor> {
    const { data } = await apiClient.request<Actor>('core', `/public/actors/${actorId}`, {
      method: 'GET',
      requiresAuth: true,
    });
    return data;
  },

  /**
   * POST /public/actors/new
   */
  async createActor(payload: ActorCreatePayload): Promise<{ status: string; message: string; actor?: Actor }> {
    const { data } = await apiClient.request('core', '/public/actors/new', {
      method: 'POST',
      body: payload,
      requiresAuth: true,
    });
    return data;
  },

  /**
   * DELETE /public/actors/delete/{actor_id}
   */
  async deleteActor(actorId: string): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.request('core', `/public/actors/delete/${actorId}`, {
      method: 'DELETE',
      requiresAuth: true,
    });
    return data;
  },

  // --- SEGMENTOS DE ACTOR (/public/actor_segments) ---

  /**
   * GET /public/actor_segments/all
   */
  async getSegments(): Promise<ActorSegment[]> {
    const { data } = await apiClient.request<ActorSegment[]>('core', '/public/actor_segments/all', {
      method: 'GET',
      requiresAuth: true,
    });
    return data;
  },

  /**
   * GET /public/actor_segments/{actor_segment_id}
   */
  async getSegmentById(segmentId: string): Promise<ActorSegment> {
    const { data } = await apiClient.request<ActorSegment>('core', `/public/actor_segments/${segmentId}`, {
      method: 'GET',
      requiresAuth: true,
    });
    return data;
  },

  /**
   * POST /public/actor_segments/new
   */
  async createSegment(payload: ActorSegmentCreatePayload): Promise<{ status: string; message: string; segment?: ActorSegment }> {
    const { data } = await apiClient.request('core', '/public/actor_segments/new', {
      method: 'POST',
      body: payload,
      requiresAuth: true,
    });
    return data;
  },

  /**
   * DELETE /public/actor_segments/delete/{actor_segment_id}
   */
  async deleteSegment(segmentId: string): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.request('core', `/public/actor_segments/delete/${segmentId}`, {
      method: 'DELETE',
      requiresAuth: true,
    });
    return data;
  },

  // --- FORMULARIOS (/public/forms) ---

  /**
   * POST /public/forms
   * Sends the full nested JSON structure: form -> sections (recursive) -> questions -> card_template -> field_groups -> fields -> field_choices
   */
  async createForm(formData: IIPForm): Promise<{ id: string; code: string; label: string; description: string | null; updated_at?: string }> {
    const { data } = await apiClient.request('core', '/public/forms', {
      method: 'POST',
      body: toCreateFormRequest(formData as IIPForm),
      requiresAuth: true,
    });
    return data;
  },

  /**
   * PUT /public/forms/{form_id}
   * Reemplaza la estructura. El backend responde 409 FORM_HAS_SUBMISSIONS_ERROR si ya tiene respuestas.
   */
  async updateForm(formId: string, formData: IIPForm): Promise<{ id: string; code: string; updated_at?: string }> {
    const { data } = await apiClient.request('core', `/public/forms/${formId}`, {
      method: 'PUT',
      body: toCreateFormRequest(formData),
      requiresAuth: true,
    });
    return data;
  },

  /** GET /public/forms — todos los formularios del backend, más recientes primero. */
  async listForms(): Promise<FormSummary[]> {
    const { data } = await apiClient.request<FormSummary[]>('core', '/public/forms', {
      method: 'GET',
      requiresAuth: true,
    });
    return data;
  },

  // ---------------------------------------------------------------- cargas históricas (solo admin)

  /** GET /public/forms/historical — formularios con estado de edición y datos cargados. */
  async listHistoricalForms(): Promise<HistoricalForm[]> {
    const { data } = await apiClient.request<HistoricalForm[]>('core', '/public/forms/historical', {
      method: 'GET',
      requiresAuth: true,
    });
    return data;
  },

  /** GET /public/forms/historical/records — entidad × formulario con respuestas y/o resultados. */
  async listRecords(): Promise<MonitorRecord[]> {
    const { data } = await apiClient.request<MonitorRecord[]>('core', '/public/forms/historical/records', {
      method: 'GET',
      requiresAuth: true,
    });
    return data;
  },

  /** GET /public/forms/{form}/historical/results/{actor} — resultado estadístico cargado (solo admin). */
  async getEntityResults(formId: string, actorId: string): Promise<EntityResults> {
    const { data } = await apiClient.request<EntityResults>(
      'core',
      `/public/forms/${formId}/historical/results/${actorId}`,
      { method: 'GET', requiresAuth: true }
    );
    return { ...data, sections: data.sections ?? [], questions: data.questions ?? [] };
  },

  /** POST /public/forms/{id}/edition/close — da por terminada la edición (habilita las plantillas). */
  async closeFormEdition(formId: string): Promise<HistoricalForm> {
    const { data } = await apiClient.request<HistoricalForm>('core', `/public/forms/${formId}/edition/close`, {
      method: 'POST',
      requiresAuth: true,
    });
    return data;
  },

  /** POST /public/forms/{id}/edition/reopen — solo si no hay respuestas ni resultados cargados. */
  async reopenFormEdition(formId: string): Promise<HistoricalForm> {
    const { data } = await apiClient.request<HistoricalForm>('core', `/public/forms/${formId}/edition/reopen`, {
      method: 'POST',
      requiresAuth: true,
    });
    return data;
  },

  /** Descarga la plantilla Excel de respuestas o de resultados del formulario. */
  async downloadHistoricalTemplate(formId: string, kind: 'responses' | 'results'): Promise<{ blob: Blob; filename: string }> {
    const { data, headers } = await apiClient.request<Blob>(
      'core',
      `/public/forms/${formId}/historical/templates/${kind}`,
      { method: 'GET', requiresAuth: true, asBlob: true }
    );
    const disposition = headers.get('content-disposition') ?? '';
    const filename = /filename="?([^";]+)"?/i.exec(disposition)?.[1] ?? `plantilla_${kind}.xlsx`;
    return { blob: data, filename };
  },

  /**
   * Valida (dry_run) o carga un Excel de respuestas / resultados históricos.
   * Con errores no se guarda nada: el reporte indica hoja, fila y columna.
   */
  async uploadHistorical(
    formId: string,
    kind: 'responses' | 'results',
    file: File,
    opts: { dryRun: boolean; replace?: boolean }
  ): Promise<HistoricalReport> {
    const formData = new FormData();
    formData.append('file', file);
    const qs = new URLSearchParams({ dry_run: String(opts.dryRun) });
    if (kind === 'responses' && opts.replace) qs.set('replace', 'true');
    const { data } = await apiClient.request<HistoricalReport>(
      'core',
      `/public/forms/${formId}/historical/${kind}?${qs.toString()}`,
      { method: 'POST', requiresAuth: true, formData }
    );
    return data;
  },

  /** GET /public/forms/{form_id} — árbol completo del formulario, ya en el modelo del frontend. */
  async getForm(formId: string): Promise<IIPForm> {
    const { data } = await apiClient.request<FormTree>('core', `/public/forms/${formId}`, {
      method: 'GET',
      requiresAuth: true,
    });
    return fromFormTree(data);
  },

  /**
   * DELETE /public/forms/{form_id}
   * Solo administradores; 409 FORM_HAS_SUBMISSIONS_ERROR si ya tiene respuestas.
   */
  async deleteForm(formId: string): Promise<void> {
    await apiClient.request('core', `/public/forms/${formId}`, {
      method: 'DELETE',
      requiresAuth: true,
    });
  },

  /** GET /public/forms/lookup/{code} — null si el formulario aún no existe en el backend. */
  async getFormStatus(code: string): Promise<FormStatus | null> {
    try {
      const { data } = await apiClient.request<FormStatus>('core', `/public/forms/lookup/${encodeURIComponent(code)}`, {
        method: 'GET',
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err?.status === 404) return null;
      throw err;
    }
  },

  /** GET /public/forms/file-types */
  async getFileTypes(): Promise<FileTypeInfo[]> {
    const { data } = await apiClient.request<FileTypeInfo[]>('core', '/public/forms/file-types', {
      method: 'GET',
      requiresAuth: true,
    });
    return data;
  },

  // --- ENVÍOS / RESPUESTAS (/public/submissions) ---

  /** GET /public/submissions — admin: todos los radicados; entidad: los suyos (sin respuestas). */
  async listSubmissions(): Promise<EntitySubmission[]> {
    const { data } = await apiClient.request<SubmissionSummaryApi[]>('core', '/public/submissions', {
      method: 'GET',
      requiresAuth: true,
    });
    return data.map(mapSubmissionSummary);
  },

  /**
   * DELETE /public/submissions/{id} — borra el radicado y sus respuestas (solo admin).
   * 409 SUBMISSION_HAS_GRADES_ERROR si ya tiene calificaciones, salvo `force`.
   */
  async deleteSubmission(id: string, force = false): Promise<void> {
    await apiClient.request('core', `/public/submissions/${id}${force ? '?force=true' : ''}`, {
      method: 'DELETE',
      requiresAuth: true,
    });
  },

  /** GET /public/submissions/{id} — radicado con sus respuestas legibles. */
  async getSubmission(id: string): Promise<EntitySubmission> {
    const { data } = await apiClient.request<SubmissionDetailApi>('core', `/public/submissions/${id}`, {
      method: 'GET',
      requiresAuth: true,
    });
    return mapSubmissionDetail(data);
  },

  /**
   * POST /public/submissions/forms/{form_id}[?as_draft=true]
   * Body: List of typed answers (boolean, text, numeric, date, single_choice, multi_choice, file, card_entry).
   * 422 si no coincide con el formulario; 409 si la entidad ya radicó este formulario.
   */
  async submitForm(
    formId: string,
    payload: SubmissionItem[],
    asDraft = false
  ): Promise<{ message: string; submission_id: string; submission_status: 'draft' | 'submitted' }> {
    const { data } = await apiClient.request<{
      message: string;
      submission_id: string;
      submission_status: 'draft' | 'submitted';
    }>('core', `/public/submissions/forms/${formId}${asDraft ? '?as_draft=true' : ''}`, {
      method: 'POST',
      body: payload,
      requiresAuth: true,
    });
    return data;
  },
};
