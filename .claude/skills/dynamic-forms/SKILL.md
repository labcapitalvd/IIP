---
name: dynamic-forms
description: Cómo se modelan y renderizan los formularios dinámicos del IIP (Componente → Variable → Indicador → Preguntas), dependencias, bucles/fichas, validación, progreso y borradores. Usar al tocar el diligenciamiento de entidades o el constructor de formularios.
---

# Formularios dinámicos IIP

## Modelo (`src/types/index.ts`)
`IIPForm.sections` = **Componentes** → `children` = **Variables** → `children` = **Indicadores** → `questions`. Solo los indicadores tienen preguntas. Cada nivel tiene `label`, `description`, `help_text` (ayuda independiente por nivel).

`FormQuestion`: `question_kind` (text, numeric, single_choice, multi_choice, boolean, file, loop), `card_template.field_groups[].fields[]`, `depends_on` (bucle que solo aplica si otra pregunta Sí/No tiene ese valor), `source_question_id` (fichas colgadas de fichas de otra pregunta).

## Lógica (`src/utils/guidedForm.ts`, sin React)
- `buildIndicatorRefs(form, selectedIds)` recorrido plano de indicadores de los componentes elegidos.
- `activeQuestions` aplica `depends_on` y descarta `file` (el diligenciamiento no maneja evidencias).
- `validateIndicator` → errores con claves `field.id`, `${card.id}_${field.id}` o `question.id`.
- `indicatorProgress` / `progressOf` → % de indicadores completos.

## Estado (`FormSubmissionContext`)
`answers` (por field id), `cardEntries` (por question id), `selectedComponentIds`, `saveDraft()` (POST `?as_draft=true`), `submitForm()`. El payload excluye preguntas inactivas y componentes no elegidos. Borrador local en `localStorage` + borrador en servidor.

## Backend
- `PUT /public/forms/assignments/{id}/components` guarda la selección de componentes (`links.user_form_assignments.selected_component_ids`).
- `GET /public/forms/assignments/me` devuelve `selected_component_ids`.

## Reglas
Nunca cargar archivos aquí; no renderizar campos `file`. Cambiar de indicador debe refrescar la ayuda (HelpPanel se reinicia por `indicator.id`).
