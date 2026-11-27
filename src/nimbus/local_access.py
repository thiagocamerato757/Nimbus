"""Local HTTP protection shared by every route (ADR-0033)."""

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

LOCAL_HOSTS = {"127.0.0.1", "localhost"}
LOCAL_ORIGINS = {f"http://{host}:{port}" for host in LOCAL_HOSTS for port in (5173, 8000)}
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class LocalAccess:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        host = headers.get("host", "").split(":")
        origin = headers.get("origin")
        if (
            host[0] not in LOCAL_HOSTS
            or len(host) > 2
            or (len(host) == 2 and host[1] not in {"5173", "8000"})
            or (origin is not None and origin not in LOCAL_ORIGINS)
            or (scope["method"] not in SAFE_METHODS and headers.get("x-nimbus-app") != "1")
        ):
            await JSONResponse(
                {"detail": {"code": "local_access", "message": "Local request checks failed."}},
                status_code=403,
            )(scope, receive, send)
            return
        await self.app(scope, receive, send)
