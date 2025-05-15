from fastapi import HTTPException, status


class PermissionDeniedException(HTTPException):
    def __init__(
        self,
        content: str = "You do not have permission to retrieve this",
        custom_message: str = "",
    ):
        full_content = (
            f"You do not have permission to {custom_message}"
            if custom_message
            else content
        )
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=full_content)


class InvalidTokenException(HTTPException):
    def __init__(
        self,
        detail: str = "Invalid token or expired",
    ):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class InvalidRefreshTokenException(HTTPException):
    def __init__(
        self,
        detail: str = "Refresh token is invalid or expired",
    ):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class InvalidCredentialsException(HTTPException):
    def __init__(
        self,
        detail: str = "Incorrect email or password",
    ):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class DisabledException(HTTPException):
    def __init__(
        self,
        detail: str = "Disabled or deleted",
    ):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class NotFoundException(HTTPException):
    def __init__(
        self,
        detail: str,
    ):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class NoContentException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_204_NO_CONTENT, detail=detail)
