import React from 'react';

/** Marca IIP: barras amarillas + «IIP» + nombre del índice. */
export const IipLogo: React.FC<{ className?: string; compact?: boolean }> = ({ className = '', compact }) => (
  <div className={`flex items-center gap-3 ${className}`}>
    <svg viewBox="0 0 36 32" className="h-8 w-9 shrink-0" aria-hidden="true">
      <rect x="1" y="18" width="8" height="13" rx="1.5" fill="#ffc400" />
      <rect x="14" y="10" width="8" height="21" rx="1.5" fill="#ffc400" />
      <rect x="27" y="1" width="8" height="30" rx="1.5" fill="#ffc400" />
    </svg>
    <span className="text-4xl font-black leading-none tracking-tight text-white">IIP</span>
    {!compact && (
      <>
        <span className="hidden h-9 w-px bg-white/30 sm:block" aria-hidden="true" />
        <span className="hidden text-sm font-semibold leading-tight text-white sm:block">
          Índice de
          <br />
          Innovación
          <br />
          Pública
        </span>
      </>
    )}
  </div>
);
