from urllib.request import (
  Request,
  HTTPRedirectHandler,
  HTTPDefaultErrorHandler,
  OpenerDirector,
  HTTPSHandler,
  HTTPErrorProcessor,
  UnknownHandler,
)


def request(
    url: str,
    method: str = "GET",
    headers: dict = {},
    data: bytes = None,
):
    method = method.upper()

    opener = OpenerDirector()
    add = opener.add_handler
    add(HTTPRedirectHandler())
    add(HTTPSHandler())
    add(HTTPDefaultErrorHandler())
    add(HTTPErrorProcessor())
    add(UnknownHandler())

    req = Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    return opener.open(req)
