import os
import json as js
import logging

from codeqlsummarize.models import CodeQLDatabase


logger = logging.getLogger("codeqlsummaries.exporters.json")


def exportToJson(database: CodeQLDatabase, output: str, **kargs):
    logger.info("Running export to JSON")
    output_file = os.path.join(output, "codeql.json")

    data = {}
    for name, summary in database.summaries.items():
        data[name] = summary.rows

    with open(output_file, "w") as handle:
        js.dump(data, handle, indent=2, sort_keys=True)

    logger.info("Completed writing to output")

    return
