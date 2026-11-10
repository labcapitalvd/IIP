---
name: design-system-iip
description: Identidad visual del Índice de Innovación Pública (IIP): tokens de color, tipografía, radios, componentes base (encabezado, stepper, tarjetas, barras de progreso, botones). Usar al dar estilo a cualquier pantalla de la entidad.
---

# Sistema de diseño IIP

Tokens definidos en `src/index.css` (`@theme`), disponibles como utilidades Tailwind (`bg-iip-navy`, `text-iip-ink`…):

| Token | Valor | Uso |
|---|---|---|
| `iip-navy` | #0d2a57 | encabezado, componente activo, iconos |
| `iip-navy-700` | #163a70 | foco, enlaces, borde seleccionado |
| `iip-yellow` | #ffc400 | acción primaria, etapa/variable activa, progreso |
| `iip-yellow-50` | #fff7d6 | «Aspectos a considerar» |
| `iip-green` | #1f9d55 | completado |
| `iip-sky` | #e8f1ff | opción seleccionada |
| `iip-bg` / `iip-line` | #f4f6fb / #dfe5ef | fondo y bordes |
| `iip-ink` / `iip-muted` | #14213d / #5b6678 | texto principal / secundario |

## Patrones
- **Encabezado**: fondo navy, logo IIP (`IipLogo`), franja amarilla diagonal, usuario + entidad a la derecha.
- **Stepper** de 5 etapas: Información general → Componentes → Diligenciamiento → Revisión → Envío (verde = hecha, amarillo = actual, gris = pendiente).
- **Tarjetas**: `rounded-3xl border border-iip-line bg-white shadow-sm`.
- **Botón primario**: `bg-iip-yellow font-extrabold text-iip-ink rounded-xl`; secundario: borde `iip-line` fondo blanco.
- **Progreso**: `IipProgress` (amarillo en curso, verde al completar).
- Tamaño mínimo de texto de lectura 15px; contraste AA sobre fondos claros.
