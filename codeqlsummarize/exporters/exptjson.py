import os
import json as js
import logging

from codeqlsummarize.models import CodeQLDatabase


logger = logging.getLogger("codeqlsummarize.exporters.json")


def exportToJson(database: CodeQLDatabase, output: str, **kargs):
    """Export to JSON"""
    logger.info("Running export to JSON")

    data = {}
    for name, summary in database.summaries.items():
        data[name] = summary.rows

    logger.info(f"Saving output to file: {output}")
    with open(output, "w") as handle:
        js.dump(data, handle, indent=2, sort_keys=True)

    logger.info("Completed writing to output")

    return
