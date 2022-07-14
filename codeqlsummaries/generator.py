

# File from CodeQL GitHub repo
# https://github.com/github/codeql/blob/main/misc/scripts/models-as-data/generate_flow_model.py

import json
import os
import os.path
import shlex
import subprocess
import tempfile
import logging

from codeqlsummaries.models import CodeQLDatabase, Summaries

logger = logging.getLogger("codeqlsummaries.generator")


QUERIES = {
    "sinks": "CaptureSinkModels.ql"
}

class Generator:
    CODEQL_LOCATION = "./codeql"
    CODEQL_REPO = "https://github.com/github/codeql.git"

    def __init__ (self, database: CodeQLDatabase):
        self.database = database 
        # working temp dir
        self.workDir = tempfile.mkdtemp()
        

    def getCodeQLRepo(self):
        cmd = ["git", "clone", "--depth", "1", Generator.CODEQL_REPO, Generator.CODEQL_LOCATION]
        with open(os.devnull, "w") as null:
            ret = subprocess.run(cmd, stdout=null)
            if ret != 0:
                raise Exception("Error getting CodeQL repo")
        return Generator

    def getModelGeneratorQuery(self, name):
        file = QUERIES.get(name)
        # os.path.join?
        return f"{Generator.CODEQL_LOCATION}/{self.database.language}/ql/src/utils/model-generator{file}"

    def runQuery(self, query: str) -> Summaries:
        logger.info("Running Query :: " + query)
        resultBqrs = os.path.join(self.workDir, "out.bqrs")
        cmd = ['codeql', 'query', 'run', query, '--database',
               self.database, '--output', resultBqrs, '--threads', '8']

        ret = subprocess.call(cmd)
        if ret != 0:
            raise Exception("Failed to generate " + query)

        rows = self.readRows(resultBqrs)

        return Summaries(rows)


    def readRows(self, bqrsFile):
        generatedJson = os.path.join(self.workDir, "out.json")
        cmd = ['codeql', 'bqrs', 'decode', bqrsFile,
               '--format=json', '--output', generatedJson]
        ret = subprocess.call(cmd)
        if ret != 0:
            raise Exception("Failed to decode BQRS. Failed command was: " + shlex.join(cmd))

        with open(generatedJson) as f:
            results = json.load(f)

        try:
            results['#select']['tuples']
        except KeyError:
            raise Exception('Unexpected JSON output - no tuples found')

        rows = ""
        for (row) in results['#select']['tuples']:
            rows += "            \"" + row[0] + "\",\n"

        return rows[:-2]

