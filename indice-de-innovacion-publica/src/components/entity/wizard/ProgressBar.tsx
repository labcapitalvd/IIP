import React from 'react';

/** Barra de progreso accesible (role=progressbar). */
export const IipProgress: React.FC<{ value: number; label: string; className?: string; tone?: 'yellow' | 'green' }> = ({
  value,
  label,
  className = '',
  tone = 'yellow',
}) => (
  <div
    role="progressbar"
    aria-label={label}
    aria-valuenow={value}
    aria-valuemin={0}
    aria-valuemax={100}
    className={`h-2.5 w-full overflow-hidden rounded-full bg-slate-200 ${className}`}
  >
    <div
      className={`h-full rounded-full transition-all duration-300 ${tone === 'green' ? 'bg-iip-green' : 'bg-iip-yellow'}`}
      style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
    />
  </div>
);
