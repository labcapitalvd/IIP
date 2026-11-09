import React from 'react';
import { LogOut, UserCircle2 } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { IipLogo } from './IipLogo';

export const WizardHeader: React.FC<{ onExit: () => void }> = ({ onExit }) => {
  const { user, logout, isLoading } = useAuth();
  return (
    <header className="relative overflow-hidden bg-iip-navy">
      <div className="pointer-events-none absolute inset-y-0 right-[22%] hidden w-10 -skew-x-[28deg] bg-iip-yellow md:block" aria-hidden="true" />
      <div className="relative mx-auto flex max-w-[1500px] items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <button type="button" onClick={onExit} className="iip-focus rounded-lg" aria-label="Volver a mis formularios">
          <IipLogo />
        </button>
        <div className="flex items-center gap-3">
          <UserCircle2 className="h-10 w-10 shrink-0 text-white" aria-hidden="true" />
          <div className="min-w-0 text-right sm:text-left">
            <p className="truncate text-sm font-bold text-white sm:text-base">{user?.contact_person || user?.username}</p>
            <p className="truncate text-xs text-white/80 sm:text-sm">{user?.actor_label || 'Entidad pública'}</p>
          </div>
          <button
            type="button"
            onClick={() => logout()}
            disabled={isLoading}
            title="Cerrar sesión"
            aria-label="Cerrar sesión"
            className="iip-focus ml-1 rounded-lg p-2 text-white/80 hover:bg-white/10 hover:text-white disabled:opacity-50"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
};
