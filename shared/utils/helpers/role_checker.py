from app.utils.exeptions import PermissionDeniedException


def check_role_creation_permissions(creator_role: int, new_user_role: int) -> None:
    if creator_role == 0:
        return

    if creator_role == 1:
        # Administrador solo puede crear Gerentes (2) o Evaluadores (3).
        if new_user_role not in [2, 3]:
            raise PermissionDeniedException(
                custom_message="No tienes permisos para crear este rol"
            )

    # Gerente y Evaluador no pueden crear ningún usuario.
    if creator_role in [2, 3]:
        raise PermissionDeniedException(
            custom_message="No tienes permisos para crear usuarios"
        )
