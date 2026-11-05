import { apiClient } from './apiClient';
import {
  Actor,
  ActorCreatePayload,
  ActorSegment,
  ActorSegmentCreatePayload,
  EntityAssignment,
  FormAssignment,
  FileTypeInfo,
  FormStatus,
  FormSummary,
  FormTree,
  IIPForm,
  SubmissionItem,
} from '../types';
import { fromFormTree, toCreateFormRequest } from '../utils/formTree';

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

  /**
   * POST /public/submissions/forms/{form_id}
   * Body: List of typed answers (boolean, text, numeric, date, singlechoice, card_entry)
   */
  async submitForm(formId: string, payload: SubmissionItem[]): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.request('core', `/public/submissions/forms/${formId}`, {
      method: 'POST',
      body: payload,
      requiresAuth: true,
    });
    return data;
  },
};
