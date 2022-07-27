import os
import json
import logging
from argparse import ArgumentParser

from codeqlsummaries import __MODULE_PATH__
from codeqlsummaries.generator import Generator, QUERIES
from codeqlsummaries.models import CodeQLDatabase, GitHub, CODEQL_LANGUAGES
from codeqlsummaries.exports import *

logger = logging.getLogger("main")

EXPORTERS = {"json": exportToJson, "customizations": exportCustomizations, "bundle": exportBundle}

parser = ArgumentParser("codeqlsummaries", "CodeQL Summary Generator")
parser.add_argument(
    "--debug", action="store_true", default=bool(os.environ.get("DEBUG"))
)
parser.add_argument("-m", "--mode", type=str, help="Mode to run the tool in")
parser.add_argument(
    "-f",
    "--format",
    default="customizations",
    help="Export format (`customizations`, `mad`, `bundle`)",
)
parser.add_argument("-i", "--input")
parser.add_argument("-o", "--output", default=os.getcwd())
parser.add_argument("--working", default=os.getcwd())

parser_codeql = parser.add_argument_group("CodeQL")
parser_codeql.add_argument("-db", "--database", help="CodeQL Database Location")
parser_codeql.add_argument("-l", "--language", help="CodeQL Database Language")

parser_github = parser.add_argument_group("GitHub")
parser_github.add_argument(
    "-r",
    "--repository",
    default=os.environ.get("GITHUB_REPOSITORY"),
    help="GitHb Repository",
)
parser_github.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN"))




if __name__ == "__main__":
    arguments = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if arguments.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    github = None

    if arguments.repository:
        owner, repo = arguments.repository.split("/", 1)
        logger.info(f"GitHub repo present - Owner: {owner}, Repository: {repo}")
        github = GitHub(
            owner=owner,
            repo=repo,
            token=arguments.github_token
        )
    if arguments.output:
        os.makedirs(arguments.output, exist_ok=True)

    databases = []
 
    # Check input file or manual
    if arguments.input:
        if not os.path.exists(arguments.input):
            raise Exception("Input file is invalid")
        with open(arguments.input, "r") as handle:
            projects = json.load(handle)
        logger.info(f"Loaded input / repo file :: {arguments.input}")
        for lang, repos in projects.items():
            for repo in repos:
                _, name = repo.split("/")
                db = CodeQLDatabase(
                    name=name,
                    language=lang,
                    repository=repo
                )
                if github and db.repository:
                    logger.info(f"Downloading database for :: {repo}")
                    download_path = db.downloadDatabase(
                        github,
                        arguments.output
                    )
                    db.path = download_path

                databases.append(db)

        logger.info("Finished loading databases from input file")

    elif arguments.database and arguments.language:
        # find local db + language
        database = CodeQLDatabase("test", arguments.database, arguments.language)
        databases.append(database)

        logger.info("Finished loading database from path")

    else:
        raise Exception("Database / Language not set")

    logger.debug(f"Databases to process :: {len(databases)}")

    for database in databases:
        logger.info(f"Database setup complete: {database}")
        
        if not database.exists():
            raise Exception("CodeQL Database does not exist...")

        # find codeql
        generator = Generator(database)

        # generate models
        # https://github.com/github/codeql/blob/main/misc/scripts/models-as-data/generate_flow_model.py

        for name, query in QUERIES.items():
            query_path = generator.getModelGeneratorQuery(name)
            if not query_path:
                continue
            database.summaries[name] = generator.runQuery(query_path)

            # temp
            for summary, data in database.summaries.items():
                logger.info(f" Summary('{summary}', rows='{len(data.rows)}')")

                with open("./test.txt", "w") as handle:
                    handle.writelines(data.rows)

        # Export to Customizations.qll file / MaD YM
        if not arguments.output:
            raise Exception("Output not set")
        exporter = EXPORTERS.get(arguments.format)
        if not exporter:
            raise Exception("Unknown or Unsupported exporter")

        exporter(
            database,
            arguments.output,
            github=github,
            working=arguments.working
        )

