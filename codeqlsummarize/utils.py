import os
import logging
from typing import *
from urllib.request import (
    Request,
    HTTPRedirectHandler,
    HTTPDefaultErrorHandler,
    OpenerDirector,
    HTTPSHandler,
    HTTPErrorProcessor,
    UnknownHandler,
)


logger = logging.getLogger("codeqlsummarize.utils")


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


def loadYaml(path: str) -> Any:
    """ Loading YAML files
    """
    try:
        # TODO: Replace with a native solution
        import yaml
    except Exception as err:
        logger.warning(f"Failed to load YAML parser: {err}")
        return

    with open(path, "r") as handle:
        return yaml.safe_load(handle)


def detectLanguage(database: str = "", project_repo: str = "", github = None) -> Optional[list[str]]:
    """ Detect languages based on:
    - the database
    - the repo languages
    """
    schema_path = os.path.join(database, "codeql-database.yml")

    if os.path.exists(schema_path):
        schema = loadYaml(schema_path)
        if schema and schema.get("primaryLanguage"):
            return [schema.get("primaryLanguage")]
    if project_repo:
        # TODO: get from GitHub API languages
        pass
    return
