---
name: frontend-design
description: Guía para construir pantallas del frontend IIP (React 19 + Vite + Tailwind 4): estructura de componentes, responsive, accesibilidad y estados de carga/guardado. Usar al crear o modificar vistas en indice-de-innovacion-publica/src.
---

# Frontend IIP — criterios de diseño

Stack real: **React 19 + Vite + Tailwind 4 + lucide-react**, router propio (`src/utils/router.ts`), estado en contextos (`AuthContext`, `AppContext`, `FormSubmissionContext`). No es Angular.

## Reglas
- Un componente = una responsabilidad; lógica pura (sin React) en `src/utils/` (ej. `guidedForm.ts`), UI en `src/components/<área>/`.
- Reutilizar antes de crear: `FormIcon`, `IipProgress`, `FieldInput`, `HelpPanel`.
- No romper lo existente: el portal admin y los contextos no se reescriben; se extienden.
- **Accesibilidad**: `role="progressbar"` con `aria-valuenow`, radios/checkboxes nativos (input `sr-only` + indicador visual), `aria-invalid`/`aria-describedby` en errores, `role="alert"` para errores y `aria-live="polite"` para guardado, foco visible (`.iip-focus`), `aria-current="step"` en navegación por etapas, respetar `prefers-reduced-motion`.
- **Responsive**: móvil primero; las columnas del tablero se apilan por debajo de `lg`; el footer de acciones es `sticky`.
- **Estados**: toda acción asíncrona muestra cargando (spinner + texto) y resultado (guardado/error). Nunca fallar en silencio.
- Textos en español; sin carga de archivos/evidencias en el flujo de diligenciamiento.
- Verificar: `npm run lint` (tsc) y `npm run build`; probar el flujo en el navegador.
