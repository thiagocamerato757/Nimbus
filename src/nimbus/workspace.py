"""A consistent snapshot for reads and atomic version-checked HTTP writes.

Every handler using this app's Store joins the request transaction. Buffering
JSON responses lets us commit before reporting success; failed handlers roll back.
"""

from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from nimbus.local_access import SAFE_METHODS
from nimbus.store import Store


class Workspace:
    def __init__(self, app: ASGIApp, store: Store):
        self.app = app
        self.store = store

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            await self.app(scope, receive, send)
            return
        writing = scope["method"] not in SAFE_METHODS
        connection = await run_in_threadpool(self.store.begin_request, writing)
        token = self.store.active.set(connection)
        messages: list[Message] = []

        async def collect(message: Message) -> None:
            messages.append(message)

        try:
            version = connection.execute("SELECT version FROM workspace_version").fetchone()[0]
            expected = Headers(scope=scope).get("x-nimbus-version")
            if writing and expected != str(version):
                await JSONResponse(
                    {
                        "detail": {
                            "code": "stale_version",
                            "message": "This edit is outdated. Review the latest state and try again.",
                        }
                    },
                    status_code=409,
                )(scope, receive, collect)
            else:
                await self.app(scope, receive, collect)
            start = next(
                message for message in messages if message["type"] == "http.response.start"
            )
            if writing and 200 <= start["status"] < 300:
                connection.execute("UPDATE workspace_version SET version = version + 1")
                connection.commit()
                version += 1
            else:
                connection.rollback()
            headers = MutableHeaders(scope=start)
            headers["x-nimbus-version"] = str(version)
            headers["cache-control"] = "no-store"
        finally:
            self.store.active.reset(token)
            connection.close()
        for message in messages:
            await send(message)
