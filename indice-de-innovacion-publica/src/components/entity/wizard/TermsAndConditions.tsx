import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ShieldCheck } from 'lucide-react';
import { TERMS_FOOTER, TERMS_SECTIONS, TERMS_TITLE } from '../../../data/privacyTerms';

/** Términos y privacidad: resumen visible con «Leer más» para desplegar el texto completo. */
export const TermsAndConditions: React.FC = () => {
  const [open, setOpen] = useState(false);
  return (
    <section aria-labelledby="terms-title" className="mt-6 rounded-2xl border border-iip-line">
      <div className="flex items-start gap-3 p-4 pb-2">
        <ShieldCheck className="mt-0.5 h-6 w-6 shrink-0 text-iip-navy" aria-hidden="true" />
        <h3 id="terms-title" className="text-base font-extrabold leading-snug text-iip-ink">{TERMS_TITLE}</h3>
      </div>

      <div className="relative px-4">
        <div
          id="terms-body"
          tabIndex={open ? 0 : -1}
          className={`space-y-5 overflow-y-auto text-sm leading-relaxed text-iip-ink transition-[max-height] ${open ? 'max-h-[28rem] pr-2' : 'max-h-40 overflow-hidden'}`}
        >
          {TERMS_SECTIONS.map((s) => (
            <div key={s.title}>
              <h4 className="font-bold">{s.title}</h4>
              <div className="mt-1.5 space-y-2">
                {s.blocks.map((b, i) =>
                  b.t === 'p' ? (
                    <p key={i}>{b.x}</p>
                  ) : (
                    <ul key={i} className="list-disc space-y-1 pl-5 marker:text-iip-yellow-600">
                      {b.x.map((li) => <li key={li}>{li}</li>)}
                    </ul>
                  )
                )}
              </div>
            </div>
          ))}
          <dl className="space-y-1 border-t border-iip-line pt-3">
            {TERMS_FOOTER.map(([k, v]) => (
              <div key={k}><dt className="inline font-bold">{k}: </dt><dd className="inline">{v}.</dd></div>
            ))}
          </dl>
        </div>
        {!open && <div className="pointer-events-none absolute inset-x-4 bottom-0 h-16 bg-gradient-to-t from-white to-transparent" aria-hidden="true" />}
      </div>

      <div className="p-4 pt-2">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="terms-body"
          className="iip-focus flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-bold text-iip-navy-700 hover:bg-iip-sky"
        >
          {open ? <>Leer menos <ChevronUp className="h-4 w-4" aria-hidden="true" /></> : <>Leer más <ChevronDown className="h-4 w-4" aria-hidden="true" /></>}
        </button>
      </div>
    </section>
  );
};
