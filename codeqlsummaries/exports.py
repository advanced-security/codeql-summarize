import json
import logging
from dataclasses import asdict
from codeqlsummaries.models import CodeQLDatabase


logger = logging.getLogger("codeqlsummaries.exporters")


def exportToJson(database: CodeQLDatabase, output: str, **kargs):
    logger.info("Running export to JSON")
    data = {}
    for name, summary in database.summaries.items():
        data[name] = summary.rows

    with open(output, "w") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)

    logger.info("Completed writing to output")

    return
