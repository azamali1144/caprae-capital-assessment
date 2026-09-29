from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Anything we want to show the client as {error: {code, message}}."""

    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class NotFound(AppError):
    def __init__(self, what: str = "Resource"):
        super().__init__("NOT_FOUND", f"{what} not found.", status.HTTP_404_NOT_FOUND)


def _body(code: str, message: str, **extra) -> dict:
    return {"error": {"code": code, "message": message, **extra}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(_body(exc.code, exc.message), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        msg = f"{where}: {first.get('msg', 'invalid input')}" if where else "Invalid input."
        return JSONResponse(
            _body("VALIDATION_ERROR", msg, details=exc.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
