# File from CodeQL GitHub repo
# https://github.com/github/codeql/blob/main/misc/scripts/models-as-data/generate_flow_model.py

import json
import os
from os.path import (
  join,
  exists,
  realpath
)
import shlex
import tempfile
import logging
from typing import *
from codeqlsummarize.utils import (
  findCodeQLCli,
  exec_from_path_env,
  print_to_stream,
)
from codeqlsummarize import __MODULE_PATH__
from codeqlsummarize.models import CodeQLDatabase, Summaries

logger = logging.getLogger("codeqlsummarize.generator")


# https://github.com/github/codeql/tree/main/java/ql/src/utils/model-generator
QUERIES = {
    "SinkModel": "CaptureSinkModels.ql",
    "SourceModel": "CaptureSourceModels.ql",
    "SummaryModel": "CaptureSummaryModels.ql",
}


class Generator:
    CODEQL_LOCATION = realpath(join(__MODULE_PATH__, "..", "codeql"))
    CODEQL_REPO = "https://github.com/github/codeql.git"

    TEMP_PATH = join(tempfile.gettempdir(), "codeqlsummarize")

    codeql: Optional[str] = None

    def __init__(self, database: CodeQLDatabase):
        self.database = database
        self.codeql = findCodeQLCli()
        if not self.codeql:
            raise Exception('Failed to find CodeQL distribution!')

    @staticmethod
    def getCodeQLRepo():
        if exists(Generator.CODEQL_LOCATION):
            logger.warning(f"CodeQL already exists, not getting latest...")
            return

        logger.info(f"Downloading CodeQL repo to :: {Generator.CODEQL_LOCATION}")
        git = exec_from_path_env('git')
        git(
            "clone",
            "--depth", "1",
            Generator.CODEQL_REPO,
            Generator.CODEQL_LOCATION,
        )
        return Generator

    def getModelGeneratorQuery(self, name) -> Optional[str]:
        logger.info(f"Finding query name: {name}")
        query_path = None
        # Find in CodeQL
        query_file = QUERIES.get(name)

        if query_file:
            query_path = f"{Generator.CODEQL_LOCATION}/{self.database.language}/ql/src/utils/model-generator/{query_file}"
            if exists(query_path):
                return query_path

        # Find in this repo
        return

    def runQuery(self, query: str) -> Summaries:
        logger.info("Running Query :: " + query)
        resultBqrs = join(Generator.TEMP_PATH, "out.bqrs")
        output_std = join(Generator.TEMP_PATH, "runquery.txt")

        with open(output_std, "wb") as std:
            self.codeql(
                "query", "run",
                "--database", self.database.path,
                "--output", resultBqrs,
                "--threads", "0",
                query,
                outconsumer=print_to_stream(std),
            )

        rows = self.readRows(resultBqrs)

        return Summaries(rows)

    def readRows(self, bqrsFile):
        logger.debug(f"Processing rows")
        # //"package;type;overrides;name;signature;ext;spec;kind"
        generatedJson = join(Generator.TEMP_PATH, "out.json")
        output_std = join(Generator.TEMP_PATH, "rows.txt")

        with open(output_std, "wb") as std:
            self.codeql(
                "bqrs", "decode",
                "--format", "json",
                "--output", generatedJson,
                bqrsFile,
                outconsumer=print_to_stream(std),
            )

        logger.debug(f"writing json output to: {generatedJson}")
        with open(generatedJson) as f:
            results = json.load(f)

        try:
            results["#select"]["tuples"]
        except KeyError:
            raise Exception("Unexpected JSON output - no tuples found")

        rows = []
        for tup in results["#select"]["tuples"]:
            rows.extend(tup)

        logger.debug(f"Final Row Summary count: {len(rows)}")

        return rows
