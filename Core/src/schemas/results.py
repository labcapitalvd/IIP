from pydantic import Field

from shared_schemas import UuidSchema

##############################################################################################
# Requests
##############################################################################################


class RequestResult(UuidSchema):
    """Modelo para representar una solicitud de índice."""
    detailed: bool = Field(
        False, description="Determinar si se desea obtener información detallada o simple."
    )
