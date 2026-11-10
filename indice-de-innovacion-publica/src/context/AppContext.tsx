import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  Actor,
  ActorCreatePayload,
  ActorSegment,
  ActorSegmentCreatePayload,
  ApiConfig,
  AuthUser,
  CreateEntityUserPayload,
  EntitySubmission,
  FormAssignment,
  HttpLog,
  IIPForm,
} from '../types';
import { IIP_DEFAULT_FORM } from '../data/defaultForm';
import { useAuth } from './AuthContext';
import { migrateForm, normalizeCodes } from '../utils/formTree';

export class FormHasSubmissionsError extends Error {
  constructor() {
    super('Este formulario ya tiene respuestas, por lo que no se puede modificar.');
    this.name = 'FormHasSubmissionsError';
  }
}
import { apiClient } from '../services/apiClient';
import { coreService } from '../services/coreService';
import { authService } from '../services/authService';

interface AppContextType {
  actors: Actor[];
  segments: ActorSegment[];
  forms: IIPForm[];
  activeForm: IIPForm;
  assignments: FormAssignment[];
  users: AuthUser[];
  submissions: EntitySubmission[];
  config: ApiConfig;
  logs: HttpLog[];
  isLoadingData: boolean;
  refreshData: () => Promise<void>;
  updateConfig: (newConfig: Partial<ApiConfig>) => void;
  clearLogs: () => void;
  // Actors
  createActor: (payload: ActorCreatePayload) => Promise<Actor>;
  deleteActor: (id: string) => Promise<void>;
  // Segments
  createSegment: (payload: ActorSegmentCreatePayload) => Promise<void>;
  deleteSegment: (id: string) => Promise<void>;
  // Forms Management (Admin creates forms)
  setActiveFormById: (formId: string) => void;
  saveFormDefinition: (form: IIPForm) => Promise<IIPForm>;
  createForm: (form: IIPForm) => Promise<void>;
  updateForm: (form: IIPForm) => Promise<void>;
  deleteForm: (id: string) => Promise<void>;
  duplicateForm: (id: string) => Promise<void>;
  // User Management (Admin creates users for entities)
  createEntityUser: (payload: CreateEntityUserPayload) => Promise<AuthUser>;
  updateEntityUser: (id: string, updates: Partial<AuthUser>) => Promise<void>;
  deleteEntityUser: (id: string) => Promise<void>;
  // Form Assignments (Admin assigns forms to entities/users)
  createAssignment: (payload: {
    form_id: string;
    user_id: string;
    actor_id: string;
    due_date: string;
    notes?: string;
  }) => Promise<void>;
  batchAssignForm: (form_id: string, user_ids: string[], due_date: string) => Promise<void>;
  removeAssignment: (id: string) => Promise<void>;
  updateAssignmentProgress: (
    actorId: string,
    formId: string,
    percentage: number,
    status?: FormAssignment['status']
  ) => void;
  completeAssignmentSubmission: (
    actorId: string,
    formId: string,
    submissionId: string,
    radicado: string,
    score?: number
  ) => void;
  // Submissions
  addSubmission: (submission: EntitySubmission) => void;
  loadSubmissionDetail: (id: string) => Promise<EntitySubmission>;
  deleteSubmission: (id: string, force?: boolean) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Legacy key: it used to hold every form; now only never-saved drafts.
const FORM_DRAFTS_KEY = 'iip_all_forms';
const ACTIVE_FORM_KEY = 'iip_active_form_id';

const readFormDrafts = (): IIPForm[] => {
  try {
    const saved = localStorage.getItem(FORM_DRAFTS_KEY);
    const parsed = saved ? (JSON.parse(saved) as IIPForm[]) : [];
    return parsed.filter((f) => !f.is_synced_to_backend).map(migrateForm);
  } catch {
    return [];
  }
};

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [config, setConfig] = useState<ApiConfig>(() => apiClient.getConfig());
  const [logs, setLogs] = useState<HttpLog[]>(() => apiClient.getLogs());

  const { user } = useAuth();

  // Actors and segments live in the backend (core service); they are loaded
  // after login by refreshData() and never cached locally.
  const [actors, setActors] = useState<Actor[]>([]);
  const [segments, setSegments] = useState<ActorSegment[]>([]);

  // Forms live in the backend and are loaded by refreshData(). Only drafts that
  // were never saved to the server (is_synced_to_backend = false) stay in this
  // browser, so a new form isn't lost before its first save.
  const [forms, setForms] = useState<IIPForm[]>(readFormDrafts);

  const [activeFormId, setActiveFormId] = useState<string | null>(() => {
    try {
      return localStorage.getItem(ACTIVE_FORM_KEY);
    } catch {
      return null;
    }
  });

  // Placeholder template only while the backend has no forms yet.
  const activeForm = forms.find((f) => f.id === activeFormId) ?? forms[0] ?? IIP_DEFAULT_FORM;

  // Usuarios de entidad: viven en el servidor (GET /auth/users, solo admin).
  const [users, setUsers] = useState<AuthUser[]>([]);

  // Asignaciones: viven en el servidor (admin: todas; entidad: las suyas).
  const [assignments, setAssignments] = useState<FormAssignment[]>([]);

  // Radicados: viven en el servidor (admin: todos; entidad: los suyos). Sin borradores.
  const [submissions, setSubmissions] = useState<EntitySubmission[]>([]);

  const [isLoadingData, setIsLoadingData] = useState(false);

  // Subscribe to HTTP logs from apiClient
  useEffect(() => {
    const unsubscribe = apiClient.subscribeLogs((newLogs) => {
      setLogs(newLogs);
    });
    return unsubscribe;
  }, []);

  // Save changes to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(
        FORM_DRAFTS_KEY,
        JSON.stringify(forms.filter((f) => !f.is_synced_to_backend))
      );
    } catch {
      // Storage unavailable (private mode, quota): drafts just won't survive a reload.
    }
  }, [forms]);

  useEffect(() => {
    try {
      if (activeFormId) localStorage.setItem(ACTIVE_FORM_KEY, activeFormId);
    } catch {
      // Remembering the selection is only a convenience.
    }
  }, [activeFormId]);

  const updateConfig = useCallback((newConfig: Partial<ApiConfig>) => {
    apiClient.updateConfig(newConfig);
    setConfig(apiClient.getConfig());
  }, []);

  const clearLogs = useCallback(() => {
    apiClient.clearLogs();
  }, []);

  const loadAssignmentsForRole = useCallback(async (u: typeof user): Promise<FormAssignment[] | null> => {
    if (!u) return null;
    try {
      if (u.role === 'admin') return await coreService.listAssignments();
      const mine = await coreService.getMyAssignments();
      return mine.map((a) => ({
        id: a.id,
        form_id: a.form_id,
        form_code: a.form_code,
        form_title: a.form_label,
        form_year: 0,
        user_id: u.id,
        user_name: u.username,
        user_email: u.email,
        actor_id: a.actor_id ?? u.actor_id ?? '',
        actor_label: a.actor_label ?? u.actor_label ?? '',
        assigned_at: a.assigned_at,
        due_date: a.due_date ?? '',
        status: a.status,
        completion_percentage: a.completion_percentage,
        submission_id: a.submission_id,
        notes: a.notes,
      }));
    } catch (err) {
      console.error('No se pudieron cargar las asignaciones del servidor:', err);
      return null;
    }
  }, []);

  const refreshAssignments = useCallback(async () => {
    const fresh = await loadAssignmentsForRole(user);
    if (fresh) setAssignments(fresh);
  }, [user, loadAssignmentsForRole]);

  const refreshData = useCallback(async () => {
    setIsLoadingData(true);
    try {
      const [fetchedActors, fetchedSegments, fetchedForms, fetchedUsers, fetchedAssignments, fetchedSubmissions] = await Promise.all([
        coreService.getActors().catch(() => [] as Actor[]),
        coreService.getSegments().catch(() => [] as ActorSegment[]),
        coreService
          .listForms()
          .then((list) => Promise.all(list.map((f) => coreService.getForm(f.id))))
          .catch((err) => {
            console.error('No se pudieron cargar los formularios del servidor:', err);
            return null;
          }),
        // Solo el admin puede listar usuarios; para una entidad el 403 es lo esperado.
        user?.role === 'admin'
          ? authService.listUsers().catch((err) => {
              console.error('No se pudieron cargar los usuarios del servidor:', err);
              return null;
            })
          : Promise.resolve(null),
        loadAssignmentsForRole(user),
        coreService
          .listSubmissions()
          .then((list) => list.filter((x) => x.status !== 'draft'))
          .catch((err) => {
            console.error('No se pudieron cargar los radicados del servidor:', err);
            return null;
          }),
      ]);
      if (fetchedSubmissions) {
        // Conserva el detalle ya cargado de los radicados que siguen existiendo.
        setSubmissions((prev) =>
          fetchedSubmissions.map((n) => prev.find((p) => p.id === n.id && p.detail_loaded) ?? n)
        );
      }
      if (fetchedUsers) setUsers(fetchedUsers);
      if (fetchedAssignments) setAssignments(fetchedAssignments);
      setActors(fetchedActors);
      setSegments(fetchedSegments);
      if (fetchedForms) {
        const serverCodes = new Set(fetchedForms.map((f) => f.code));
        setForms((prev) => [
          ...fetchedForms,
          ...prev.filter((f) => !f.is_synced_to_backend && !serverCodes.has(f.code)),
        ]);
      }
    } finally {
      setIsLoadingData(false);
    }
  }, [user?.id, user?.role, loadAssignmentsForRole]);

  // Load backend data once there is an authenticated session.
  useEffect(() => {
    if (user) refreshData();
    else {
      setActors([]);
      setSegments([]);
      setUsers([]);
      setAssignments([]);
      setSubmissions([]);
    }
  }, [user?.id, refreshData]);

  const createActor = async (payload: ActorCreatePayload): Promise<Actor> => {
    const res = await coreService.createActor(payload);
    let created: Actor;
    if (res.actor) {
      created = res.actor;
      setActors((prev) => [created, ...prev]);
    } else {
      const seg = segments.find((s) => s.id === payload.actor_segment_id);
      created = {
        id: `act-${Date.now()}`,
        label: payload.label,
        description: payload.description,
        mission: payload.mission,
        vision: payload.vision,
        actor_segment_id: payload.actor_segment_id,
        actor_segment: seg ? { id: seg.id, label: seg.label, description: seg.description } : null,
      };
      setActors((prev) => [created, ...prev]);
    }
    return created;
  };

  const deleteActor = async (id: string) => {
    await coreService.deleteActor(id);
    setActors((prev) => prev.filter((a) => a.id !== id));
  };

  const createSegment = async (payload: ActorSegmentCreatePayload) => {
    const res = await coreService.createSegment(payload);
    if (res.segment) {
      setSegments((prev) => [...prev, res.segment!]);
    } else {
      await refreshData();
    }
  };

  const deleteSegment = async (id: string) => {
    await coreService.deleteSegment(id);
    setSegments((prev) => prev.filter((s) => s.id !== id));
  };

  // Forms Management
  const setActiveFormById = useCallback((formId: string) => {
    setActiveFormId(formId);
  }, []);

  /**
   * Guarda en el backend: PUT si el formulario ya existe allí (por código), POST si no.
   * Un formulario con respuestas no se puede modificar (409 FORM_HAS_SUBMISSIONS_ERROR).
   */
  const saveFormDefinition = async (form: IIPForm): Promise<IIPForm> => {
    const normalized = normalizeCodes(form);
    const existing = await coreService.getFormStatus(normalized.code);
    if (existing && !form.is_synced_to_backend) {
      // Formulario nuevo (local) cuyo código ya existe en el servidor: no se sobrescribe en silencio.
      throw new Error(
        `Ya existe en el servidor un formulario con el código "${normalized.code}". Use otro código para este formulario.`
      );
    }
    let savedId: string;
    if (existing) {
      if (existing.has_submissions) throw new FormHasSubmissionsError();
      if (existing.edition_closed_at)
        throw new Error('La edición de este formulario está cerrada: ya no se puede modificar.');
      try {
        savedId = (await coreService.updateForm(existing.id, normalized)).id;
      } catch (err: any) {
        throw err?.data?.code === 'FORM_HAS_SUBMISSIONS_ERROR' ? new FormHasSubmissionsError() : err;
      }
    } else {
      savedId = (await coreService.createForm(normalized)).id;
    }
    // Re-read what the server stored: a PUT rebuilds the tree, so section,
    // question and field ids change, and submissions must use the new ones.
    const savedForm = await coreService.getForm(savedId);
    setForms((prev) => [savedForm, ...prev.filter((f) => f.id !== form.id && f.id !== savedForm.id)]);
    setActiveFormId(savedForm.id);
    return savedForm;
  };

  const createForm = async (form: IIPForm) => {
    await saveFormDefinition(form);
  };

  const updateForm = async (form: IIPForm) => {
    await saveFormDefinition(form);
  };

  const deleteForm = async (id: string) => {
    const target = forms.find((f) => f.id === id);
    if (target?.is_synced_to_backend) {
      try {
        await coreService.deleteForm(id);
      } catch (err: any) {
        throw err?.data?.code === 'FORM_HAS_SUBMISSIONS_ERROR' ? new FormHasSubmissionsError() : err;
      }
    }
    setForms((prev) => prev.filter((f) => f.id !== id));
  };

  /** Copia el formulario y la guarda en el servidor; si falla, queda como borrador local. */
  const duplicateForm = async (id: string) => {
    const base = forms.find((f) => f.id === id);
    if (!base) return;

    const newForm: IIPForm = {
      ...JSON.parse(JSON.stringify(base)),
      id: `form-iip-${Date.now()}`,
      code: `${base.code}_COPIA_${new Date().getFullYear()}`.slice(0, 50),
      label: `${base.label} (Copia)`,
      version: `${base.version}.1`,
      is_active: false,
      is_synced_to_backend: false,
      updated_at: null,
    };

    setForms((prev) => [newForm, ...prev]);
    await saveFormDefinition(newForm);
  };

  // User Management for Entities
  const createEntityUser = async (payload: CreateEntityUserPayload): Promise<AuthUser> => {
    // El servidor crea la cuenta (con su vínculo a la entidad); luego se relee la lista
    // para obtener el id real, que es el que usan las asignaciones.
    await authService.register({
      username: payload.username.toLowerCase().trim(),
      email: payload.email.toLowerCase().trim(),
      password: payload.password ?? '',
      actor_id: payload.actor_id,
      contact_person: payload.contact_person,
      phone: payload.phone,
    });
    const fresh = await authService.listUsers();
    setUsers(fresh);
    const newUser = fresh.find((u) => u.username === payload.username.toLowerCase().trim());
    if (!newUser) throw new Error('El usuario se creó pero no se pudo recuperar del servidor.');

    // Si se pidió asignar un formulario al crear el usuario, se guarda en el servidor.
    if (payload.assign_form_id) {
      const targetForm = forms.find((f) => f.id === payload.assign_form_id) || activeForm;
      await coreService.assignForm({
        user_id: newUser.id,
        form_id: targetForm.id,
        due_date: payload.due_date ? payload.due_date.slice(0, 10) : null,
      });
      await refreshAssignments();
    }

    return newUser;
  };

  const updateEntityUser = useCallback(async (id: string, updates: Partial<AuthUser>) => {
    await authService.updateUser(id, {
      is_active: updates.is_active,
      contact_person: updates.contact_person,
      phone: updates.phone,
    });
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, ...updates } : u)));
  }, []);

  const deleteEntityUser = useCallback(async (id: string) => {
    await authService.deleteUser(id);
    setUsers((prev) => prev.filter((u) => u.id !== id));
  }, []);

  // Form Assignments
  const createAssignment = useCallback(
    async (payload: {
      form_id: string;
      user_id: string;
      actor_id: string;
      due_date: string;
      notes?: string;
    }) => {
      await coreService.assignForm({
        user_id: payload.user_id,
        form_id: payload.form_id,
        due_date: payload.due_date.slice(0, 10),
        notes: payload.notes,
      });
      await refreshAssignments();
    },
    [refreshAssignments]
  );

  const batchAssignForm = useCallback(
    async (form_id: string, user_ids: string[], due_date: string) => {
      const results = await Promise.allSettled(
        user_ids.map((uid) =>
          coreService.assignForm({ user_id: uid, form_id, due_date: due_date.slice(0, 10) })
        )
      );
      await refreshAssignments();
      const failed = results.filter((r) => r.status === 'rejected').length;
      if (failed > 0) {
        throw new Error(`No se pudo asignar a ${failed} de ${user_ids.length} usuarios.`);
      }
    },
    [refreshAssignments]
  );

  const removeAssignment = useCallback(async (id: string) => {
    await coreService.deleteAssignment(id);
    setAssignments((prev) => prev.filter((a) => a.id !== id));
  }, []);

  const updateAssignmentProgress = useCallback(
    (actorId: string, formId: string, percentage: number, status?: FormAssignment['status']) => {
      setAssignments((prev) =>
        prev.map((a) => {
          if (a.actor_id === actorId && (a.form_id === formId || !formId)) {
            const nextStatus =
              status || (percentage >= 100 ? 'submitted' : percentage > 0 ? 'in_progress' : 'pending');
            return {
              ...a,
              completion_percentage: percentage,
              status: nextStatus,
            };
          }
          return a;
        })
      );
    },
    []
  );

  const completeAssignmentSubmission = useCallback(
    (actorId: string, formId: string, submissionId: string, radicado: string, score?: number) => {
      setAssignments((prev) =>
        prev.map((a) => {
          if (a.actor_id === actorId && (a.form_id === formId || !formId)) {
            return {
              ...a,
              status: 'submitted',
              completion_percentage: 100,
              score,
              submission_id: submissionId,
              radicado_number: radicado,
              submitted_at: new Date().toISOString(),
            };
          }
          return a;
        })
      );
    },
    []
  );

  /** Agrega (o reemplaza por id) un radicado recién creado en el servidor. */
  const addSubmission = useCallback((newSub: EntitySubmission) => {
    setSubmissions((prev) => [newSub, ...prev.filter((s) => s.id !== newSub.id)]);
  }, []);

  /** Carga del servidor las respuestas de un radicado y las deja en la lista. */
  const loadSubmissionDetail = useCallback(async (id: string): Promise<EntitySubmission> => {
    const detail = await coreService.getSubmission(id);
    setSubmissions((prev) => prev.map((s) => (s.id === id ? detail : s)));
    return detail;
  }, []);

  /** Borra el radicado en el servidor; la asignación de esa entidad vuelve a quedar pendiente. */
  const deleteSubmission = useCallback(
    async (id: string, force = false) => {
      await coreService.deleteSubmission(id, force);
      setSubmissions((prev) => prev.filter((s) => s.id !== id));
      await refreshAssignments();
    },
    [refreshAssignments]
  );

  return (
    <AppContext.Provider
      value={{
        actors,
        segments,
        forms,
        activeForm,
        assignments,
        users,
        submissions,
        config,
        logs,
        isLoadingData,
        refreshData,
        updateConfig,
        clearLogs,
        createActor,
        deleteActor,
        createSegment,
        deleteSegment,
        setActiveFormById,
        saveFormDefinition,
        createForm,
        updateForm,
        deleteForm,
        duplicateForm,
        createEntityUser,
        updateEntityUser,
        deleteEntityUser,
        createAssignment,
        batchAssignForm,
        removeAssignment,
        updateAssignmentProgress,
        completeAssignmentSubmission,
        addSubmission,
        loadSubmissionDetail,
        deleteSubmission,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
