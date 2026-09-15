import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import {
  AuthUser,
  CreateEntityUserPayload,
  ActorCreatePayload,
} from '../../types';
import {
  Users,
  UserPlus,
  Building2,
  Mail,
  Phone,
  Shield,
  Key,
  CheckCircle2,
  AlertCircle,
  Search,
  Filter,
  Trash2,
  Edit,
  ExternalLink,
  Plus,
  Layers,
  Sparkles,
  Lock,
  UserCheck,
} from 'lucide-react';

interface EntityUsersManagerProps {
  onAssignFormToUser?: (userId: string, actorId: string) => void;
}

export const EntityUsersManager: React.FC<EntityUsersManagerProps> = ({
  onAssignFormToUser,
}) => {
  const {
    users,
    actors,
    segments,
    forms,
    assignments,
    createEntityUser,
    updateEntityUser,
    deleteEntityUser,
    createActor,
  } = useApp();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSegmentFilter, setSelectedSegmentFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'active'>('all');

  // Create User Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('Bogota2026*');
  const [selectedActorId, setSelectedActorId] = useState(actors[0]?.id || '');
  const [contactPerson, setContactPerson] = useState('');
  const [phone, setPhone] = useState('');
  const [assignImmediately, setAssignImmediately] = useState(true);
  const [selectedFormId, setSelectedFormId] = useState(forms[0]?.id || '');
  const [dueDate, setDueDate] = useState('2026-09-30');

  // Quick New Entity Submodal within User Creation
  const [showNewActorModal, setShowNewActorModal] = useState(false);
  const [newActorLabel, setNewActorLabel] = useState('');
  const [newActorSegmentId, setNewActorSegmentId] = useState(segments[0]?.id || '');
  const [newActorMission, setNewActorMission] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ success: boolean; message: string } | null>(null);

  // Filter only entity users (and show admin separately if needed)
  const entityUsers = users.filter((u) => u.role === 'entity');
  const pendingUsers = entityUsers.filter((u) => u.is_active === false || u.approval_status === 'pending');
  const activeUsers = entityUsers.filter((u) => u.is_active !== false && u.approval_status !== 'pending');

  const filteredUsers = entityUsers.filter((u) => {
    const isPending = u.is_active === false || u.approval_status === 'pending';
    if (statusFilter === 'pending' && !isPending) return false;
    if (statusFilter === 'active' && isPending) return false;

    const matchesSearch =
      u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (u.actor_label && u.actor_label.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (u.contact_person && u.contact_person.toLowerCase().includes(searchTerm.toLowerCase()));

    if (selectedSegmentFilter === 'all') return matchesSearch;

    const actor = actors.find((a) => a.id === u.actor_id);
    return matchesSearch && actor?.actor_segment_id === selectedSegmentFilter;
  });

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !email.trim() || !selectedActorId) {
      setFeedback({
        success: false,
        message: 'Por favor complete el nombre de usuario, correo y seleccione una entidad.',
      });
      return;
    }

    setIsSubmitting(true);
    setFeedback(null);

    try {
      const selectedActor = actors.find((a) => a.id === selectedActorId);
      const payload: CreateEntityUserPayload = {
        username: username.trim(),
        email: email.trim(),
        password,
        actor_id: selectedActorId,
        actor_label: selectedActor?.label,
        contact_person: contactPerson.trim() || undefined,
        phone: phone.trim() || undefined,
        assign_form_id: assignImmediately ? selectedFormId : undefined,
        due_date: assignImmediately ? `${dueDate}T23:59:59Z` : undefined,
      };

      const created = await createEntityUser(payload);

      setFeedback({
        success: true,
        message: `Usuario "${created.username}" creado exitosamente para ${created.actor_label}${
          assignImmediately ? ' con formulario asignado.' : '.'
        }`,
      });

      // Reset form
      setUsername('');
      setEmail('');
      setContactPerson('');
      setPhone('');
      setShowCreateModal(false);
    } catch (err: any) {
      setFeedback({
        success: false,
        message: err?.message || 'Error al crear el usuario.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateQuickActor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newActorLabel.trim()) return;

    try {
      const payload: ActorCreatePayload = {
        label: newActorLabel.trim(),
        actor_segment_id: newActorSegmentId || null,
        description: `Entidad distrital creada por el administrador.`,
        mission: newActorMission.trim() || null,
        vision: null,
      };

      const created = await createActor(payload);
      setSelectedActorId(created.id);
      setNewActorLabel('');
      setNewActorMission('');
      setShowNewActorModal(false);
    } catch (err: any) {
      alert(err?.message || 'Error al crear entidad.');
    }
  };

  const handleApproveUser = (targetUser: AuthUser) => {
    updateEntityUser(targetUser.id, {
      is_active: true,
      approval_status: 'approved',
    });
    setFeedback({
      success: true,
      message: `Permiso concedido exitosamente: El usuario "${targetUser.username}" ahora puede ingresar a la plataforma para representar a ${targetUser.actor_label}.`,
    });
  };

  const handleToggleUserStatus = (user: AuthUser) => {
    const nextStatus = !user.is_active;
    updateEntityUser(user.id, {
      is_active: nextStatus,
      approval_status: nextStatus ? 'approved' : 'rejected',
    });
    setFeedback({
      success: true,
      message: `Estado del usuario "${user.username}" actualizado a ${nextStatus ? 'Activo / Autorizado' : 'Inactivo / Suspendido'}.`,
    });
  };

  const handleDeleteUser = (userId: string, userName: string) => {
    if (confirm(`¿Está seguro de eliminar el usuario "${userName}"?`)) {
      deleteEntityUser(userId);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-amber-600 uppercase tracking-wider bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
              Administración • LabCapital
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-600">
              Gestión de Cuentas Distritales
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
            Usuarios para Entidades Distritales
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Cree cuentas de acceso institucional asociadas a organismos distritales para el diligenciamiento del IIP.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-2"
          >
            <UserPlus className="w-4 h-4" />
            <span>Crear Usuario para Entidad</span>
          </button>
        </div>
      </div>

      {feedback && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-center gap-2 animate-in fade-in ${
            feedback.success
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {feedback.success ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Usuarios de Entidades
            </span>
            <div className="text-2xl font-black text-slate-900">{entityUsers.length}</div>
          </div>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Entidades con Usuario
            </span>
            <div className="text-2xl font-black text-slate-900">
              {new Set(entityUsers.map((u) => u.actor_id)).size}
            </div>
          </div>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-bold">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Asignaciones Activas
            </span>
            <div className="text-2xl font-black text-slate-900">{assignments.length}</div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-3">
        {/* Quick Status Filter Tabs */}
        <div className="flex flex-wrap items-center gap-2 pb-2 border-b border-slate-100">
          <button
            type="button"
            onClick={() => setStatusFilter('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              statusFilter === 'all'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <span>Todos los Usuarios</span>
            <span className="px-1.5 py-0.5 rounded-md bg-white/20 text-[10px]">
              {entityUsers.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('pending')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              statusFilter === 'pending'
                ? 'bg-amber-500 text-slate-950 shadow-xs'
                : 'bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100'
            }`}
          >
            <span>⏳ Pendientes de Autorización</span>
            <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-extrabold ${
              statusFilter === 'pending' ? 'bg-slate-950 text-amber-400' : 'bg-amber-200 text-amber-900'
            }`}>
              {pendingUsers.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setStatusFilter('active')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              statusFilter === 'active'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100'
            }`}
          >
            <span>✓ Activos / Autorizados</span>
            <span className="px-1.5 py-0.5 rounded-md bg-white/20 text-[10px]">
              {activeUsers.length}
            </span>
          </button>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar por usuario, correo o entidad..."
              className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedSegmentFilter}
              onChange={(e) => setSelectedSegmentFilter(e.target.value)}
              className="text-xs px-3 py-2 border border-slate-200 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 w-full sm:w-60"
            >
              <option value="all">Todos los Sectores Distritales</option>
              {segments.map((seg) => (
                <option key={seg.id} value={seg.id}>
                  {seg.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-6 py-4">Usuario & Credenciales</th>
                <th className="px-6 py-4">Entidad Distrital Asociada</th>
                <th className="px-6 py-4">Sector Administrativo</th>
                <th className="px-6 py-4">Contacto / Teléfono</th>
                <th className="px-6 py-4 text-center">Formularios Asignados</th>
                <th className="px-6 py-4 text-center">Estado / Autorización</th>
                <th className="px-6 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    No se encontraron usuarios de entidades con los filtros seleccionados.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => {
                  const userAssignments = assignments.filter((a) => a.user_id === user.id);
                  const actor = actors.find((a) => a.id === user.actor_id);
                  const isPending = user.is_active === false || user.approval_status === 'pending';

                  return (
                    <tr key={user.id} className={`transition-colors ${isPending ? 'bg-amber-50/30 hover:bg-amber-50/60' : 'hover:bg-slate-50/80'}`}>
                      <td className="px-6 py-4">
                        <div className="space-y-0.5">
                          <div className="font-bold text-slate-900 flex items-center gap-1.5">
                            <span className="font-mono text-amber-700">{user.username}</span>
                          </div>
                          <div className="text-[11px] text-slate-500 flex items-center gap-1">
                            <Mail className="w-3 h-3 text-slate-400" />
                            <span>{user.email}</span>
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-900 flex items-start gap-1.5 max-w-xs">
                          <Building2 className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                          <span className="truncate">{user.actor_label || actor?.label}</span>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                          {actor?.actor_segment?.label || user.actor_segment_label || 'Distrital'}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <div className="space-y-0.5 text-[11px] text-slate-600">
                          <div>{user.contact_person || 'Responsable de Innovación'}</div>
                          {user.phone && (
                            <div className="text-slate-400 flex items-center gap-1 text-[10px]">
                              <Phone className="w-2.5 h-2.5" />
                              <span>{user.phone}</span>
                            </div>
                          )}
                        </div>
                      </td>

                      <td className="px-6 py-4 text-center">
                        <span className="font-bold text-slate-900 bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-0.5 rounded-full text-xs">
                          {userAssignments.length}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-center">
                        {isPending ? (
                          <div className="inline-flex flex-col items-center gap-1">
                            <span className="px-2.5 py-1 rounded-full font-bold text-[10px] bg-amber-100 text-amber-900 border border-amber-300 shadow-xs">
                              ⏳ Pendiente de Aprobación
                            </span>
                            <span className="text-[9px] text-amber-700">Sin acceso hasta autorizar</span>
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleToggleUserStatus(user)}
                            className="px-2.5 py-0.5 rounded-full font-bold text-[10px] border border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors"
                            title="Clic para cambiar estado"
                          >
                            ● Activo / Autorizado
                          </button>
                        )}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {isPending ? (
                            <button
                              type="button"
                              onClick={() => handleApproveUser(user)}
                              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs shadow-xs flex items-center gap-1.5 transition-all"
                              title="Dar permiso de ingreso a este usuario registrado"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Autorizar Ingreso</span>
                            </button>
                          ) : (
                            onAssignFormToUser && (
                              <button
                                type="button"
                                onClick={() => onAssignFormToUser(user.id, user.actor_id || '')}
                                className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-900 font-semibold rounded-lg text-[11px] border border-amber-200 flex items-center gap-1 transition-colors"
                                title="Asignar formulario a este usuario"
                              >
                                <Sparkles className="w-3 h-3 text-amber-600" />
                                <span>Asignar</span>
                              </button>
                            )
                          )}

                          <button
                            type="button"
                            onClick={() => handleDeleteUser(user.id, user.username)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                            title="Eliminar usuario"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal to Create Entity User */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-white w-full max-w-2xl rounded-3xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between border-b border-slate-800">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-amber-500 text-slate-950 flex items-center justify-center font-bold shadow-md">
                  <UserPlus className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider block">
                    Veeduría Distrital • LabCapital
                  </span>
                  <h3 className="text-base font-bold text-white">Crear Usuario para Entidad</h3>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="p-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Nombre de Usuario (Username) <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="ej. planeacion.innovacion"
                    className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Correo Institucional <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="innovacion@planeacionbogota.gov.co"
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  />
                </div>

                <div className="sm:col-span-2">
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-bold text-slate-700">
                      Entidad Distrital Asociada <span className="text-rose-500">*</span>
                    </label>
                    <button
                      type="button"
                      onClick={() => setShowNewActorModal(true)}
                      className="text-[11px] font-bold text-amber-600 hover:text-amber-700 flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" />
                      <span>+ Crear Nueva Entidad</span>
                    </button>
                  </div>
                  <select
                    value={selectedActorId}
                    onChange={(e) => setSelectedActorId(e.target.value)}
                    className="w-full text-xs font-semibold px-3 py-2 border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  >
                    {actors.map((actor) => (
                      <option key={actor.id} value={actor.id}>
                        {actor.label}{' '}
                        {actor.actor_segment?.label ? `(${actor.actor_segment.label})` : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Persona de Contacto / Enlace
                  </label>
                  <input
                    type="text"
                    value={contactPerson}
                    onChange={(e) => setContactPerson(e.target.value)}
                    placeholder="Dra. Carolina Martínez"
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Teléfono / Extensión
                  </label>
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+57 (601) 3358000 Ext 240"
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Contraseña Inicial Temporal
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                    />
                    <Lock className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2" />
                  </div>
                </div>
              </div>

              {/* Instant Form Assignment Option */}
              <div className="p-4 bg-amber-50/60 rounded-2xl border border-amber-200/80 space-y-3">
                <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-slate-900">
                  <input
                    type="checkbox"
                    checked={assignImmediately}
                    onChange={(e) => setAssignImmediately(e.target.checked)}
                    className="rounded text-amber-600 focus:ring-amber-500 w-4 h-4"
                  />
                  <span>Asignar formulario de diagnóstico inmediatamente al crear usuario</span>
                </label>

                {assignImmediately && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-600 mb-1">
                        Formulario a Asignar
                      </label>
                      <select
                        value={selectedFormId}
                        onChange={(e) => setSelectedFormId(e.target.value)}
                        className="w-full text-xs font-semibold px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                      >
                        {forms.map((f) => (
                          <option key={f.id} value={f.id}>
                            {f.label} ({f.code})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-600 mb-1">
                        Fecha Límite de Diligenciamiento
                      </label>
                      <input
                        type="date"
                        value={dueDate}
                        onChange={(e) => setDueDate(e.target.value)}
                        className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-xl border border-slate-300 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-bold rounded-xl shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <div className="w-3.5 h-3.5 border-2 border-slate-950/30 border-t-slate-950 rounded-full animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4" />
                  )}
                  <span>Crear Usuario</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Submodal for creating a new Actor/Entity on the fly */}
      {showNewActorModal && (
        <div className="fixed inset-0 z-60 bg-slate-900/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 p-5 space-y-4 animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h4 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-amber-500" />
                <span>Registrar Nueva Entidad Distrital</span>
              </h4>
              <button
                onClick={() => setShowNewActorModal(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateQuickActor} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Nombre Oficial de la Entidad <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={newActorLabel}
                  onChange={(e) => setNewActorLabel(e.target.value)}
                  placeholder="ej. Secretaría Distrital de Salud (SDS)"
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Sector Administrativo
                </label>
                <select
                  value={newActorSegmentId}
                  onChange={(e) => setNewActorSegmentId(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white"
                >
                  {segments.map((seg) => (
                    <option key={seg.id} value={seg.id}>
                      {seg.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Misión Institucional
                </label>
                <textarea
                  rows={2}
                  value={newActorMission}
                  onChange={(e) => setNewActorMission(e.target.value)}
                  placeholder="Garantizar el derecho a la salud..."
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowNewActorModal(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs rounded-lg"
                >
                  Guardar Entidad
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
