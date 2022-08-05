# File from CodeQL GitHub repo
# https://github.com/github/codeql/blob/main/misc/scripts/models-as-data/generate_flow_model.py

import json
import os
from os.path import join, exists, realpath
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
    TEMP_PATH = join(tempfile.gettempdir(), "codeqlsummarize")

    codeql: Optional[str] = None

    def __init__(self, database: CodeQLDatabase):
        self.database = database
        self.codeql = findCodeQLCli()
        if not self.codeql:
            raise Exception("Failed to find CodeQL distribution!")

        self.pack_name = f"codeql/{database.language}-queries"
        self.codeql("pack", "download", self.pack_name)

    def getModelGeneratorQuery(self, name) -> Optional[str]:
        logger.info(f"Finding query name: {name}")
        # Find in CodeQL
        query_file = QUERIES.get(name)

        if query_file:
            return f"{self.pack_name}:utils/model-generator/{query_file}"

        # Find in this repo
        return None

    def runQuery(self, query: str) -> Summaries:
        logger.info("Running Query :: " + query)
        resultBqrs = join(
            self.database.path,
            "results",
            query.replace(":", "/").replace(".ql", ".bqrs"),
        )

        output_std = join(Generator.TEMP_PATH, "runquery.txt")

        print(f'Running query "{query}"...')
        with open(output_std, "wb") as std:
            self.codeql(
                "database",
                "run-queries",
                "--threads",
                "0",
                self.database.path,
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
                "bqrs",
                "decode",
                "--format",
                "json",
                "--output",
                generatedJson,
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
