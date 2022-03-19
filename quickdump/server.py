from typing import NamedTuple

import uvicorn
from starlette.applications import Starlette
from starlette.datastructures import URL, Headers
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from quickdump import QuickDumper, Suffix
from quickdump.const import DEFAULT_SERVER_DUMP_LABEL


class RequestDump(NamedTuple):
    url: URL
    method: str
    headers: Headers
    body: bytes


async def do_dump(request: Request) -> Response:
    if label := request.path_params.get("label"):
        dumper = QuickDumper(label, suffix=default_suffix)
    else:
        dumper = QuickDumper(DEFAULT_SERVER_DUMP_LABEL, suffix=default_suffix)

    dump = RequestDump(
        url=request.url,
        method=request.method,
        headers=request.headers,
        body=await request.body(),
    )
    dumper.dump(dump)
    return JSONResponse({"ok": "true"})


default_suffix = Suffix.Minute
app = Starlette(
    debug=True,
    routes=[
        Route("/{label}", do_dump),
        Route("/", do_dump),
    ],
)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=4410)


if __name__ == "__main__":
    main()
