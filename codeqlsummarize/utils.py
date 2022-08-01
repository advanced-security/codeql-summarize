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


logger = logging.getLogger("codeqlsummarize.generator")


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
    e = shutil.which(execname)
    return Executable(e) if e else None


def codeql_from_gh_codeql():
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
    return "codeql" + ("" if os.name == "posix" else ".exe")


def codeql_from_actions():
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
    return \
        exec_from_path_env('codeql') or \
        codeql_from_gh_codeql() or \
        codeql_from_actions()
