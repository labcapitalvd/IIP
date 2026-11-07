/**
 * Eliminar las respuestas de una entidad con las confirmaciones del monitor:
 * una confirmación y, si el servidor avisa de calificaciones (409), una segunda para borrarlas también.
 * Devuelve true si se eliminó; false si el administrador canceló.
 */
export const deleteSubmissionWithConfirm = async (
  deleteSubmission: (id: string, force?: boolean) => Promise<void>,
  submissionId: string,
  actorLabel: string,
  formCode: string
): Promise<boolean> => {
  if (
    !confirm(
      `¿Eliminar TODAS las respuestas de «${actorLabel}» al formulario «${formCode}»?\n\n` +
        'Esta acción no se puede deshacer. La asignación de esa entidad volverá a quedar pendiente. ' +
        'El resultado estadístico cargado no se modifica.'
    )
  )
    return false;
  try {
    await deleteSubmission(submissionId);
  } catch (err: any) {
    if (err?.data?.code !== 'SUBMISSION_HAS_GRADES_ERROR') throw err;
    if (!confirm('Este radicado ya tiene calificaciones. ¿Eliminarlo junto con sus calificaciones?')) return false;
    await deleteSubmission(submissionId, true);
  }
  return true;
};
