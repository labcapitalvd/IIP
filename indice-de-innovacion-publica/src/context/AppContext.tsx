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
  duplicateForm: (id: string) => void;
  // User Management (Admin creates users for entities)
  createEntityUser: (payload: CreateEntityUserPayload) => Promise<AuthUser>;
  updateEntityUser: (id: string, updates: Partial<AuthUser>) => void;
  deleteEntityUser: (id: string) => void;
  // Form Assignments (Admin assigns forms to entities/users)
  createAssignment: (payload: {
    form_id: string;
    user_id: string;
    actor_id: string;
    due_date: string;
    notes?: string;
  }) => void;
  batchAssignForm: (form_id: string, user_ids: string[], due_date: string) => void;
  removeAssignment: (id: string) => void;
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
    score: number
  ) => void;
  // Submissions
  addSubmission: (submission: EntitySubmission) => void;
  updateSubmissionStatus: (id: string, status: EntitySubmission['status']) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [config, setConfig] = useState<ApiConfig>(() => apiClient.getConfig());
  const [logs, setLogs] = useState<HttpLog[]>(() => apiClient.getLogs());

  const { user } = useAuth();

  // Actors and segments live in the backend (core service); they are loaded
  // after login by refreshData() and never cached locally.
  const [actors, setActors] = useState<Actor[]>([]);
  const [segments, setSegments] = useState<ActorSegment[]>([]);

  const [forms, setForms] = useState<IIPForm[]>(() => {
    const saved = localStorage.getItem('iip_all_forms');
    return (saved ? (JSON.parse(saved) as IIPForm[]) : [IIP_DEFAULT_FORM]).map(migrateForm);
  });

  const [activeForm, setActiveForm] = useState<IIPForm>(() => {
    const saved = localStorage.getItem('iip_active_form');
    return migrateForm(saved ? (JSON.parse(saved) as IIPForm) : IIP_DEFAULT_FORM);
  });

  const [users, setUsers] = useState<AuthUser[]>(() => {
    const saved = localStorage.getItem('iip_all_users');
    return saved ? JSON.parse(saved) : [];
  });

  const [assignments, setAssignments] = useState<FormAssignment[]>(() => {
    const saved = localStorage.getItem('iip_assignments');
    return saved ? JSON.parse(saved) : [];
  });

  const [submissions, setSubmissions] = useState<EntitySubmission[]>(() => {
    const saved = localStorage.getItem('iip_submissions');
    return saved ? JSON.parse(saved) : [];
  });

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
    localStorage.setItem('iip_all_forms', JSON.stringify(forms));
  }, [forms]);

  useEffect(() => {
    localStorage.setItem('iip_active_form', JSON.stringify(activeForm));
  }, [activeForm]);

  useEffect(() => {
    localStorage.setItem('iip_all_users', JSON.stringify(users));
  }, [users]);

  useEffect(() => {
    localStorage.setItem('iip_assignments', JSON.stringify(assignments));
  }, [assignments]);

  useEffect(() => {
    localStorage.setItem('iip_submissions', JSON.stringify(submissions));
  }, [submissions]);

  const updateConfig = useCallback((newConfig: Partial<ApiConfig>) => {
    apiClient.updateConfig(newConfig);
    setConfig(apiClient.getConfig());
  }, []);

  const clearLogs = useCallback(() => {
    apiClient.clearLogs();
  }, []);

  const refreshData = useCallback(async () => {
    setIsLoadingData(true);
    try {
      const [fetchedActors, fetchedSegments] = await Promise.all([
        coreService.getActors().catch(() => [] as Actor[]),
        coreService.getSegments().catch(() => [] as ActorSegment[]),
      ]);
      setActors(fetchedActors);
      setSegments(fetchedSegments);
    } finally {
      setIsLoadingData(false);
    }
  }, []);

  // Load backend data once there is an authenticated session.
  useEffect(() => {
    if (user) refreshData();
    else {
      setActors([]);
      setSegments([]);
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
    const found = forms.find((f) => f.id === formId);
    if (found) {
      setActiveForm(found);
    }
  }, [forms]);

  /**
   * Guarda en el backend: PUT si el formulario ya existe allí (por código), POST si no.
   * Un formulario con respuestas no se puede modificar (409 FORM_HAS_SUBMISSIONS_ERROR).
   */
  const saveFormDefinition = async (form: IIPForm): Promise<IIPForm> => {
    const normalized = normalizeCodes(form);
    const existing = await coreService.getFormStatus(normalized.code);
    let updatedAt: string | undefined;
    if (existing && !form.is_synced_to_backend) {
      // Formulario nuevo (local) cuyo código ya existe en el servidor: no se sobrescribe en silencio.
      throw new Error(
        `Ya existe en el servidor un formulario con el código "${normalized.code}". Use otro código para este formulario.`
      );
    }
    if (existing) {
      if (existing.has_submissions) throw new FormHasSubmissionsError();
      try {
        updatedAt = (await coreService.updateForm(existing.id, normalized)).updated_at;
      } catch (err: any) {
        throw err?.data?.code === 'FORM_HAS_SUBMISSIONS_ERROR' ? new FormHasSubmissionsError() : err;
      }
    } else {
      updatedAt = (await coreService.createForm(normalized)).updated_at;
    }
    const savedForm: IIPForm = {
      ...normalized,
      is_synced_to_backend: true,
      updated_at: updatedAt ?? new Date().toISOString(),
    };
    const nextForms = forms.some((f) => f.id === savedForm.id)
      ? forms.map((f) => (f.id === savedForm.id ? savedForm : f))
      : [savedForm, ...forms];
    // Persistir ya mismo: tras guardar la pantalla se recarga y no debe perderse nada.
    localStorage.setItem('iip_all_forms', JSON.stringify(nextForms));
    localStorage.setItem('iip_active_form', JSON.stringify(savedForm));
    setActiveForm(savedForm);
    setForms(nextForms);
    return savedForm;
  };

  const createForm = async (form: IIPForm) => {
    await saveFormDefinition(form);
  };

  const updateForm = async (form: IIPForm) => {
    await saveFormDefinition(form);
  };

  const deleteForm = async (id: string) => {
    setForms((prev) => prev.filter((f) => f.id !== id));
    if (activeForm.id === id) {
      const remaining = forms.filter((f) => f.id !== id);
      if (remaining.length > 0) {
        setActiveForm(remaining[0]);
      }
    }
  };

  const duplicateForm = useCallback((id: string) => {
    const base = forms.find((f) => f.id === id);
    if (!base) return;

    const newForm: IIPForm = {
      ...JSON.parse(JSON.stringify(base)),
      id: `form-iip-${Date.now()}`,
      code: `${base.code}_COPIA_${new Date().getFullYear()}`,
      label: `${base.label} (Copia)`,
      version: `${base.version}.1`,
      is_active: false,
    };

    setForms((prev) => [newForm, ...prev]);
  }, [forms]);

  // User Management for Entities
  const createEntityUser = async (payload: CreateEntityUserPayload): Promise<AuthUser> => {
    const actor = actors.find((a) => a.id === payload.actor_id);
    const newUser: AuthUser = {
      id: `usr-entity-${Date.now()}`,
      username: payload.username.toLowerCase().trim(),
      email: payload.email.toLowerCase().trim(),
      role: 'entity',
      actor_id: payload.actor_id,
      actor_label: actor?.label || payload.actor_label || 'Entidad Distrital',
      actor_segment_label: actor?.actor_segment?.label,
      is_active: true,
      created_at: new Date().toISOString(),
      phone: payload.phone,
      contact_person: payload.contact_person,
    };

    setUsers((prev) => [newUser, ...prev]);

    // If user requested to assign a form immediately upon user creation
    if (payload.assign_form_id) {
      const targetForm = forms.find((f) => f.id === payload.assign_form_id) || activeForm;
      const newAsg: FormAssignment = {
        id: `asg-${Date.now()}`,
        form_id: targetForm.id,
        form_code: targetForm.code,
        form_title: targetForm.label,
        form_year: targetForm.year,
        user_id: newUser.id,
        user_name: newUser.username,
        user_email: newUser.email,
        actor_id: newUser.actor_id!,
        actor_label: newUser.actor_label!,
        actor_segment_label: newUser.actor_segment_label,
        assigned_at: new Date().toISOString(),
        due_date: payload.due_date || new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'pending',
        completion_percentage: 0,
      };
      setAssignments((prev) => [newAsg, ...prev]);
    }

    return newUser;
  };

  const updateEntityUser = useCallback((id: string, updates: Partial<AuthUser>) => {
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, ...updates } : u)));
  }, []);

  const deleteEntityUser = useCallback((id: string) => {
    setUsers((prev) => prev.filter((u) => u.id !== id));
  }, []);

  // Form Assignments
  const createAssignment = useCallback(
    (payload: {
      form_id: string;
      user_id: string;
      actor_id: string;
      due_date: string;
      notes?: string;
    }) => {
      const form = forms.find((f) => f.id === payload.form_id) || activeForm;
      const userObj = users.find((u) => u.id === payload.user_id);
      const actor = actors.find((a) => a.id === payload.actor_id);

      const newAsg: FormAssignment = {
        id: `asg-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
        form_id: form.id,
        form_code: form.code,
        form_title: form.label,
        form_year: form.year,
        user_id: payload.user_id,
        user_name: userObj?.username || 'entidad.usuario',
        user_email: userObj?.email || 'entidad@bogota.gov.co',
        actor_id: payload.actor_id,
        actor_label: actor?.label || userObj?.actor_label || 'Entidad Distrital',
        actor_segment_label: actor?.actor_segment?.label,
        assigned_at: new Date().toISOString(),
        due_date: payload.due_date,
        status: 'pending',
        completion_percentage: 0,
        notes: payload.notes,
      };

      setAssignments((prev) => {
        // Prevent exact duplicate for same form and user
        const filtered = prev.filter(
          (a) => !(a.form_id === payload.form_id && a.user_id === payload.user_id)
        );
        return [newAsg, ...filtered];
      });
    },
    [forms, activeForm, users, actors]
  );

  const batchAssignForm = useCallback(
    (form_id: string, user_ids: string[], due_date: string) => {
      const form = forms.find((f) => f.id === form_id) || activeForm;
      const newAsgs: FormAssignment[] = [];

      for (const uid of user_ids) {
        const u = users.find((usr) => usr.id === uid);
        if (!u || !u.actor_id) continue;
        const actor = actors.find((a) => a.id === u.actor_id);

        newAsgs.push({
          id: `asg-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
          form_id: form.id,
          form_code: form.code,
          form_title: form.label,
          form_year: form.year,
          user_id: u.id,
          user_name: u.username,
          user_email: u.email,
          actor_id: u.actor_id,
          actor_label: actor?.label || u.actor_label || 'Entidad Distrital',
          actor_segment_label: actor?.actor_segment?.label,
          assigned_at: new Date().toISOString(),
          due_date: due_date,
          status: 'pending',
          completion_percentage: 0,
        });
      }

      setAssignments((prev) => {
        const existingKeys = new Set(newAsgs.map((na) => `${na.form_id}_${na.user_id}`));
        const filtered = prev.filter((a) => !existingKeys.has(`${a.form_id}_${a.user_id}`));
        return [...newAsgs, ...filtered];
      });
    },
    [forms, activeForm, users, actors]
  );

  const removeAssignment = useCallback((id: string) => {
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
    (actorId: string, formId: string, submissionId: string, radicado: string, score: number) => {
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

  const addSubmission = useCallback((newSub: EntitySubmission) => {
    setSubmissions((prev) => [newSub, ...prev]);
  }, []);

  const updateSubmissionStatus = useCallback((id: string, status: EntitySubmission['status']) => {
    setSubmissions((prev) => prev.map((s) => (s.id === id ? { ...s, status } : s)));
  }, []);

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
        updateSubmissionStatus,
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
