import React, { useEffect, useState } from 'react';
import { AlertCircle, Building2, Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { coreService } from '../../services/coreService';
import { Actor } from '../../types';

const Row: React.FC<{ label: string; value?: string | null }> = ({ label, value }) => (
  <div className="py-3 border-b border-gray-100 last:border-0">
    <dt className="text-xs font-medium text-gray-500">{label}</dt>
    <dd className="text-sm text-gray-800 mt-0.5 whitespace-pre-line">{value || '—'}</dd>
  </div>
);

export const EntityAccountView: React.FC = () => {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Perfil</h2>
        <p className="text-sm text-gray-500 mt-1">Datos de tu cuenta en la plataforma.</p>
      </div>
      <dl className="rounded-2xl border border-gray-200 px-5">
        <Row label="Usuario" value={user.username} />
        <Row label="Correo electrónico" value={user.email} />
        <Row label="Nombre" value={user.contact_person} />
        <Row label="Teléfono" value={user.phone} />
        <Row label="Entidad" value={user.actor_label} />
      </dl>
    </div>
  );
};

export const EntityAssignedActorView: React.FC = () => {
  const { user } = useAuth();
  const [actor, setActor] = useState<Actor | null>(null);
  const [loading, setLoading] = useState(!!user?.actor_id);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user?.actor_id) return;
    let alive = true;
    coreService
      .getActorById(user.actor_id)
      .then((a) => alive && setActor(a))
      .catch((e) => alive && setError(e?.message || 'No se pudo cargar la entidad.'))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [user?.actor_id]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Entidad asignada</h2>
        <p className="text-sm text-gray-500 mt-1">Entidad distrital a la que perteneces.</p>
      </div>

      {!user?.actor_id ? (
        <p className="py-10 text-center text-sm text-gray-500">Tu cuenta aún no tiene una entidad asignada.</p>
      ) : loading ? (
        <div className="flex items-center justify-center gap-2 py-16 text-gray-500 text-sm">
          <Loader2 className="w-5 h-5 animate-spin text-blue-600" /> Cargando entidad…
        </div>
      ) : error ? (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-700 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : (
        actor && (
          <div className="rounded-2xl border border-gray-200 p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-200">
                <Building2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-base font-bold text-gray-800 capitalize">{actor.label}</h3>
                <span className="text-xs text-gray-500">{actor.actor_segment?.label || 'Sin segmento'}</span>
              </div>
            </div>
            <dl>
              <Row label="Descripción" value={actor.description} />
              <Row label="Misión" value={actor.mission} />
              <Row label="Visión" value={actor.vision} />
            </dl>
          </div>
        )
      )}
    </div>
  );
};
