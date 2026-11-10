import React, { useEffect, useState } from 'react';
import { Layers, Lightbulb, ListChecks, Target, Workflow } from 'lucide-react';
import { FormSection } from '../../../types';

type Level = 'indicator' | 'variable' | 'component';

interface HelpPanelProps {
  component: FormSection;
  variable: FormSection;
  indicator: FormSection;
}

const LEVELS: { id: Level; label: string; icon: React.ElementType }[] = [
  { id: 'indicator', label: 'Indicador', icon: Target },
  { id: 'variable', label: 'Variable', icon: Workflow },
  { id: 'component', label: 'Componente', icon: Layers },
];

const BULLET = /^\s*(?:[-•*]|\d+[.)])\s+/;

/** Separa la ayuda en un párrafo introductorio y una lista de «aspectos a considerar» (líneas con viñeta). */
const parseHelp = (text?: string | null) => {
  const lines = (text ?? '').split('\n').map((l) => l.trim()).filter(Boolean);
  return {
    paragraphs: lines.filter((l) => !BULLET.test(l)),
    bullets: lines.filter((l) => BULLET.test(l)).map((l) => l.replace(BULLET, '')),
  };
};

/**
 * Ayuda contextual con tres niveles independientes (Componente, Variable, Indicador).
 * Cada nivel lee solo su propia descripción/ayuda; al cambiar de indicador el panel se actualiza
 * y vuelve al nivel Indicador.
 */
export const HelpPanel: React.FC<HelpPanelProps> = ({ component, variable, indicator }) => {
  const [level, setLevel] = useState<Level>('indicator');
  useEffect(() => setLevel('indicator'), [indicator.id]);

  const section = level === 'indicator' ? indicator : level === 'variable' ? variable : component;
  const levelLabel = LEVELS.find((l) => l.id === level)!.label;
  const { paragraphs, bullets } = parseHelp(section.help_text);
  const hasContent = !!section.description || paragraphs.length > 0 || bullets.length > 0;

  return (
    <aside aria-label="Ayuda contextual" className="rounded-3xl border border-iip-line bg-white p-4 shadow-sm sm:p-5">
      <div role="tablist" aria-label="Nivel de ayuda" className="grid grid-cols-3 gap-1 rounded-2xl bg-iip-bg p-1">
        {LEVELS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            role="tab"
            type="button"
            id={`help-tab-${id}`}
            aria-selected={level === id}
            aria-controls="help-panel"
            onClick={() => setLevel(id)}
            className={`iip-focus flex items-center justify-center gap-1.5 rounded-xl px-2 py-2.5 text-sm font-bold transition-colors ${
              level === id ? 'bg-iip-yellow text-iip-ink shadow-sm' : 'text-iip-muted hover:bg-white'
            }`}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span className="truncate">{label}</span>
          </button>
        ))}
      </div>

      <div id="help-panel" role="tabpanel" aria-labelledby={`help-tab-${level}`} aria-live="polite" className="mt-5 space-y-4">
        <div className="flex items-start gap-2.5">
          <Lightbulb className="mt-0.5 h-6 w-6 shrink-0 text-iip-navy" aria-hidden="true" />
          <div>
            <h3 className="text-lg font-bold leading-tight text-iip-ink">Ayuda del {levelLabel.toLowerCase()}</h3>
            <p className="text-sm font-semibold text-iip-muted">{section.label}</p>
          </div>
        </div>

        {!hasContent && (
          <p className="rounded-2xl bg-iip-bg p-4 text-sm text-iip-muted">
            Este {levelLabel.toLowerCase()} aún no tiene una guía publicada. Responda según la información de su entidad.
          </p>
        )}

        {section.description && <p className="text-[15px] leading-relaxed text-iip-ink">{section.description}</p>}
        {paragraphs.map((p, i) => (
          <p key={i} className="text-[15px] leading-relaxed text-iip-ink">{p}</p>
        ))}

        {bullets.length > 0 && (
          <div className="rounded-2xl bg-iip-yellow-50 p-4">
            <p className="flex items-center gap-2 text-sm font-bold text-iip-ink">
              <ListChecks className="h-5 w-5 text-iip-yellow-600" aria-hidden="true" />
              Aspectos a considerar:
            </p>
            <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-snug text-iip-ink marker:text-iip-yellow-600">
              {bullets.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </aside>
  );
};
