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
import subprocess
from subprocess import CalledProcessError
import glob
import os.path
import shutil
import logging
import threading
import json
import os
import io


logger = logging.getLogger("codeqlsummarize.utils")


logger = logging.getLogger("codeqlsummarize.utils")


def request(
    url: str,
    method: str = "GET",
    headers: dict = {},
    data: Optional[bytes] = None,
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
    
def print_to_stream(f):
    def impl(cmd, stream):
        while True:
            chunk = stream.readline()
            if chunk == b'':
                break
            f.write(chunk)
            f.flush()
        stream.close()
    return impl


def close_stream(cmd, stream):
    stream.close()


class Executable:
    def __init__(self, executable):
        self.executable = executable

    def __call__(
        self,
        *args,
        outconsumer=None,
        errconsumer=None,
        combine_std_out_err=True,
        inprovider=close_stream,
        cwd='.',
        **kwargs
    ):
        with open(os.devnull, 'wb') as devnull:
            outconsumer = outconsumer or print_to_stream(devnull)
            errconsumer = errconsumer or print_to_stream(devnull)

            outpipe = subprocess.PIPE
            errpipe = subprocess.PIPE
            if combine_std_out_err:
                errpipe = subprocess.STDOUT
            inpipe = subprocess.PIPE
            command = [self.executable] + list(args)

            with subprocess.Popen(
                command,
                stdout=outpipe,
                stderr=errpipe,
                stdin=inpipe,
                cwd=cwd,
            ) as proc:

              commandstr = ' '.join(command)
              tout = threading.Thread(target=outconsumer, args=(commandstr, proc.stdout))
              tout.start()
              terr = None
              if not combine_std_out_err:
                  terr = threading.Thread(target=errconsumer, args=(commandstr, proc.stderr))
                  terr.start()
              tin = threading.Thread(target=inprovider, args=(commandstr, proc.stdin))
              tin.start()

              ret = proc.wait()
              tout.join()
              tin.join()
              if terr:
                  terr.join()
              if ret != 0:
                  raise CalledProcessError(cmd=commandstr, returncode=ret)


def exec_from_path_env(execname):
    """ Find CodeQL in PATH
    """
    e = shutil.which(execname)
    return Executable(e) if e else None


def codeql_from_gh_codeql():
    """ Find CodeQL using GitHub CLI CodeQL Extension
    """
    gh = exec_from_path_env('gh')
    if gh:
        try:
            output = io.BytesIO()
            gh(
                'codeql',
                'version',
                '--format', 'json',
                combine_std_out_err=False,
                outconsumer=print_to_stream(output)
            )
            output.seek(0)
            return Executable(
                os.path.join(
                    json.load(output)['unpackedLocation'],
                    codeql_exec_name(),
                )
            )
        except CalledProcessError:
            return None
    return None


def codeql_exec_name():
    """ Check CodeQL CLI name based on OS Type
    """
    return "codeql" + ("" if os.name == "posix" else ".exe")


def codeql_from_actions():
    """ Find CodeQL in GitHub Actions
    """
    actions = glob.glob(
        os.path.join(
            os.environ.get("RUNNER_TOOL_CACHE", ""),
            "CodeQL",
            "*",
            "x64",
            "codeql",
            codeql_exec_name(),
        )
    )
    if len(actions) != 0:
        logger.debug(f"CodeQL found on Actions :: {actions[0]}")
        return Executable(actions[0])
    return None


def findCodeQLCli():
    """ Find CodeQL executable
    """
    return \
        exec_from_path_env(codeql_exec_name()) or \
        codeql_from_gh_codeql() or \
        codeql_from_actions()

