import { apiClient } from './apiClient';
import {
  Actor,
  ActorCreatePayload,
  ActorSegment,
  ActorSegmentCreatePayload,
  IIPForm,
  SubmissionItem,
} from '../types';

export const coreService = {
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
  async createForm(formData: Partial<IIPForm>): Promise<{ id: string; code: string; label: string; description: string | null }> {
    const { data } = await apiClient.request('core', '/public/forms', {
      method: 'POST',
      body: formData,
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
