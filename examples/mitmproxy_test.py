import quickdump

qd = quickdump.QuickDumper("mitm_test")

from mitmproxy import http


def response(flow: http.HTTPFlow) -> None:
    print("flowing!")
    qd("hello")
    qd(flow)
    if flow.response and flow.response.content:
        flow.response.content = flow.response.content.replace(
            b"</head>", b"<style>body {transform: scaleX(-1);}</style></head>"
        )


# addons = [
#     MyAddon()
# ]
