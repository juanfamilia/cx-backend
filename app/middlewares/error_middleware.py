from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.core.db import get_db


async def db_exception_handler(request: Request, call_next):
    try:
        session_generator = get_db()
        session = await session_generator.__anext__()

        response = await call_next(request)

        add_cors_headers(response, request)

        return response

    except IntegrityError as e:
        if session:
            await session.rollback()
        response = handle_integrity_error(e, request)
        add_cors_headers(response, request)
        return response

    except SQLAlchemyError as e:
        if session:
            await session.rollback()
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Database error occurred: {e}"},
        )
        add_cors_headers(response, request)
        return response

    except ValueError as e:
        response = JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(e)},
        )
        add_cors_headers(response, request)
        return response

    except Exception as e:
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(e)},
        )
        add_cors_headers(response, request)
        return response


# Función para agregar los headers CORS manualmente
def add_cors_headers(response, request: Request):
    # Puedes modificar esta lógica si necesitas añadir más cosas
    origin = request.headers.get("Origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


def handle_integrity_error(exc: IntegrityError, request: Request) -> JSONResponse:
    conflict_fields = [
        "email",
        "identity_number",
        "fiscal_code",
        "sanity_code",
    ]

    if "ForeignKeyViolationError" in str(exc.orig):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "ForeignKeyViolationError: The value violates a foreign key constraint"
            },
        )

    for field in conflict_fields:
        if field in str(exc.orig):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": f"The {field.replace('_', ' ')} is already in use"},
            )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )
