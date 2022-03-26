import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import uvicorn
from multidict import CIMultiDict
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.endpoints import HTTPEndpoint

from quickdump import QuickDumper
from quickdump.const import _default_label


@dataclass
class RequestDump:
    headers: CIMultiDict[str]
    url: str
    body: bytes
    dumped_at: datetime = field(default_factory=datetime.now)

    @property
    def json(self) -> Any:
        return json.loads(self.body)


class DumpApp(HTTPEndpoint):
    async def dispatch(self) -> None:
        request = Request(self.scope, receive=self.receive)

        label = request.path_params.get("label") or _default_label
        print(request.path_params)
        print(request.url)

        dumper = QuickDumper(label)

        body = await request.body()
        headers = CIMultiDict(request.headers)
        url = request.url

        req_dump = RequestDump(headers=headers, url=str(url), body=body)
        dumper.dump(req_dump)

        response = Response(status_code=201)
        await response(self.scope, self.receive, self.send)


app = Starlette(
    debug=True,
    routes=[
        Route("/{full_path:path}", DumpApp),
        # Route("/", DumpApp),
    ],
)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=4410)


if __name__ == "__main__":
    main()
