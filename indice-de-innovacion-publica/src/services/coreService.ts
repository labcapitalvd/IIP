import { apiClient } from './apiClient';
import {
  Actor,
  ActorCreatePayload,
  ActorSegment,
  ActorSegmentCreatePayload,
  IIPForm,
  SubmissionItem,
} from '../types';
import { INITIAL_ACTORS, INITIAL_ACTOR_SEGMENTS } from '../data/mockData';

export const coreService = {
  // --- ACTORES (/public/actors) ---

  /**
   * GET /public/actors/all
   */
  async getActors(): Promise<Actor[]> {
    try {
      const { data } = await apiClient.request<Actor[]>('core', '/public/actors/all', {
        method: 'GET',
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        const saved = localStorage.getItem('iip_mock_actors');
        return saved ? JSON.parse(saved) : INITIAL_ACTORS;
      }
      throw err;
    }
  },

  /**
   * GET /public/actors/{actor_id}
   */
  async getActorById(actorId: string): Promise<Actor> {
    try {
      const { data } = await apiClient.request<Actor>('core', `/public/actors/${actorId}`, {
        method: 'GET',
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        const actors = await this.getActors();
        const found = actors.find((a) => a.id === actorId);
        if (!found) throw new Error('Actor no encontrado');
        return found;
      }
      throw err;
    }
  },

  /**
   * POST /public/actors/new
   */
  async createActor(payload: ActorCreatePayload): Promise<{ status: string; message: string; actor?: Actor }> {
    try {
      const { data } = await apiClient.request('core', '/public/actors/new', {
        method: 'POST',
        body: payload,
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        const current = await this.getActors();
        const newActor: Actor = {
          id: payload.id || `act-${Date.now()}`,
          label: payload.label,
          description: payload.description,
          mission: payload.mission,
          vision: payload.vision,
          actor_segment_id: payload.actor_segment_id,
        };
        const updated = [newActor, ...current];
        localStorage.setItem('iip_mock_actors', JSON.stringify(updated));
        return { status: 'success', message: 'Actor creado exitosamente', actor: newActor };
      }
      throw err;
    }
  },

  /**
   * DELETE /public/actors/delete/{actor_id}
   */
  async deleteActor(actorId: string): Promise<{ status: string; message: string }> {
    try {
      const { data } = await apiClient.request('core', `/public/actors/delete/${actorId}`, {
        method: 'DELETE',
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        const current = await this.getActors();
        const filtered = current.filter((a) => a.id !== actorId);
        localStorage.setItem('iip_mock_actors', JSON.stringify(filtered));
        return { status: 'success', message: 'Actor eliminado exitosamente' };
      }
      throw err;
    }
  },

  // --- SEGMENTOS DE ACTOR (/public/actor_segments) ---

  /**
   * GET /public/actor_segments/all
   */
  async getSegments(): Promise<ActorSegment[]> {
    try {
      const { data } = await apiClient.request<ActorSegment[]>('core', '/public/actor_segments/all', {
        method: 'GET',
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        const saved = localStorage.getItem('iip_mock_segments');
        return saved ? JSON.parse(saved) : INITIAL_ACTOR_SEGMENTS;
      }
      throw err;
    }
  },

  /**
   * GET /public/actor_segments/{actor_segment_id}
   */
  async getSegmentById(segmentId: string): Promise<ActorSegment> {
    try {
      const { data } = await apiClient.request<ActorSegment>('core', `/public/actor_segments/${segmentId}`, {
        method: 'GET',
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        const segments = await this.getSegments();
        const found = segments.find((s) => s.id === segmentId);
        if (!found) throw new Error('Segmento no encontrado');
        return found;
      }
      throw err;
    }
  },

  /**
   * POST /public/actor_segments/new
   */
  async createSegment(payload: ActorSegmentCreatePayload): Promise<{ status: string; message: string; segment?: ActorSegment }> {
    try {
      const { data } = await apiClient.request('core', '/public/actor_segments/new', {
        method: 'POST',
        body: payload,
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        const current = await this.getSegments();
        const newSeg: ActorSegment = {
          id: payload.id || `seg-${Date.now()}`,
          label: payload.label,
          description: payload.description,
        };
        const updated = [...current, newSeg];
        localStorage.setItem('iip_mock_segments', JSON.stringify(updated));
        return { status: 'success', message: 'Segmento creado exitosamente', segment: newSeg };
      }
      throw err;
    }
  },

  /**
   * DELETE /public/actor_segments/delete/{actor_segment_id}
   */
  async deleteSegment(segmentId: string): Promise<{ status: string; message: string }> {
    try {
      const { data } = await apiClient.request('core', `/public/actor_segments/delete/${segmentId}`, {
        method: 'DELETE',
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        const current = await this.getSegments();
        const filtered = current.filter((s) => s.id !== segmentId);
        localStorage.setItem('iip_mock_segments', JSON.stringify(filtered));
        return { status: 'success', message: 'Segmento eliminado exitosamente' };
      }
      throw err;
    }
  },

  // --- FORMULARIOS (/public/forms) ---

  /**
   * POST /public/forms
   * Sends the full nested JSON structure: form -> sections (recursive) -> questions -> card_template -> field_groups -> fields -> field_choices
   */
  async createForm(formData: Partial<IIPForm>): Promise<{ id: string; code: string; label: string; description: string | null }> {
    try {
      const { data } = await apiClient.request('core', '/public/forms', {
        method: 'POST',
        body: formData,
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        return {
          id: formData.id || `form-${Date.now()}`,
          code: formData.code || 'FORM_CUSTOM',
          label: formData.label || 'Formulario Personalizado IIP',
          description: formData.description || null,
        };
      }
      throw err;
    }
  },

  // --- ENVÍOS / RESPUESTAS (/public/submissions) ---

  /**
   * POST /public/submissions/forms/{form_id}
   * Body: List of typed answers (boolean, text, numeric, date, singlechoice, card_entry)
   */
  async submitForm(formId: string, payload: SubmissionItem[]): Promise<{ status: string; message: string }> {
    try {
      const { data } = await apiClient.request('core', `/public/submissions/forms/${formId}`, {
        method: 'POST',
        body: payload,
        requiresAuth: true,
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        return {
          status: 'success',
          message: `submission ${formId} created (mock local registration).`,
        };
      }
      throw err;
    }
  },
};
