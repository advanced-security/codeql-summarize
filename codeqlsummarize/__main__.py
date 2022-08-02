import os
import sys
import json
import logging
import tempfile
from argparse import ArgumentParser

sys.path.append(".")

from codeqlsummarize import __MODULE_PATH__
from codeqlsummarize.generator import Generator, QUERIES
from codeqlsummarize.models import CodeQLDatabase, GitHub
from codeqlsummarize.exporters import EXPORTERS
from codeqlsummarize.utils import detectLanguage

logger = logging.getLogger("main")


parser = ArgumentParser("codeql-summarize", "CodeQL Summary Generator")
parser.add_argument(
    "--debug", action="store_true", default=bool(os.environ.get("DEBUG"))
)
parser.add_argument(
    "-f",
    "--format",
    default="bundle",
    help="Export format (`json`, `customizations`, `mad`, `bundle`)",
)
parser.add_argument("-i", "--input", help="Input / Project File")
parser.add_argument("-o", "--output", default=os.getcwd(), help="Output directory / file")

parser.add_argument("--disable-cache", action="store_true")

parser_codeql = parser.add_argument_group("CodeQL")
parser_codeql.add_argument("--codeql-base", default="./codeql", help="CodeQL Base Path")
parser_codeql.add_argument("-p", "--project-repo", help="Project Repo")
parser_codeql.add_argument("-db", "--database", help="CodeQL Database Location")
parser_codeql.add_argument("-l", "--language", help="CodeQL Database Language")

parser_github = parser.add_argument_group("GitHub")
parser_github.add_argument(
    "-r",
    "--github-repository",
    default=os.environ.get("GITHUB_REPOSITORY"),
    help="GitHb Repository",
)
parser_github.add_argument(
    "-t", "--github-token", default=os.environ.get("GITHUB_TOKEN")
)

def main(arguments):
    """ Main workflow
    """
    github = GitHub(token=arguments.github_token)
    languages: list[str] = []
    databases: list[CodeQLDatabase] = []

    logging.basicConfig(
        level=logging.DEBUG if arguments.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.debug("Debugging is enabled")

    if not arguments.format:
        raise Exception("Format flag is not set")

    if not EXPORTERS.get(arguments.format):
        raise Exception(f"Format mode provided isn't valid: {arguments.format}")

    # Support for Actions temp dirs
    temppath = os.path.join(
        os.environ.get("RUNNER_TEMP", tempfile.gettempdir()), "codeqlsummarize"
    )
    os.makedirs(temppath, exist_ok=True)
    Generator.TEMP_PATH = temppath

    if arguments.language:
        languages.extend(arguments.language.split(","))

    elif (arguments.database or arguments.project_repo) and not arguments.language:
        logger.info(f"Language not detected, running auto-detect...")
        langs = detectLanguage(
            database=arguments.database, project_repo=arguments.project_repo
        )

        if langs:
            languages.extend(langs)

    if arguments.github_repository:
        owner, repo = arguments.github_repository.split("/", 1)
        logger.info(f"GitHub repo present - Owner: {owner}, Repository: {repo}")
        github.owner = owner
        github.repo = repo

    if arguments.output:
        output = os.path.splitext(arguments.output)
        if output[1] != "":
            logger.debug(f"Output is a file")
        else:
            logger.debug(f"Creating output dir :: {arguments.output}")
            os.makedirs(arguments.output, exist_ok=True)
    else:
        raise Exception("Output is not set")

    # If scan repo settings are present
    if arguments.project_repo:
        _, repo = arguments.project_repo.split("/", 1)

        for language in languages:
            logger.info(
                f"Analysing remote repo: {arguments.project_repo} ({language})"
            )

            database = CodeQLDatabase(
                repo, language=language, repository=arguments.project_repo
            )

            if github.avalible:
                database.path = database.downloadDatabase(github, temppath)
            elif arguments.database:
                logger.debug("Setting database to arguments.database ")
                database.path = arguments.database
            else:
                logger.warning(f"Failed to download or find database path...")

            databases.append(database)

    # If a project file is present
    elif arguments.input:
        """Input file is a `projects.json` file"""
        # TODO: Schema check?
        logger.info(f"Loaded input / projects file :: {arguments.input}")

        if not os.path.exists(arguments.input):
            raise Exception("Input file is invalid")
        with open(arguments.input, "r") as handle:
            projects = json.load(handle)

        for lang, repos in projects.items():
            for repo in repos:
                _, name = repo.split("/")

                db = CodeQLDatabase(name=name, language=lang, repository=repo)

                if github.avalible and db.repository:
                    logger.info(f"Downloading database for :: {repo}")

                    download_path = db.downloadDatabase(
                        github, temppath, use_cache=not arguments.disable_cache
                    )

                    db.path = download_path

                if not db.path:
                    logger.warning(f"CodeQL Database path is not set")

                databases.append(db)

        logger.info("Finished loading databases from input file")

    elif arguments.database:
        for language in languages:
            # find local db + language
            database = CodeQLDatabase(
                "test", path=arguments.database, language=language
            )
            databases.append(database)

        logger.info("Finished loading database from path")

    else:
        raise Exception("Failed to set mode of analysis")

    logger.info(f"Databases to process :: {len(databases)}")

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

        for summary, data in database.summaries.items():
            logger.info(f" Summary('{summary}', rows='{len(data.rows)}')")

        logger.info(f"Running exporter :: {arguments.format}")

        exporter = EXPORTERS.get(arguments.format)
        if not exporter:
            raise Exception("Unknown or Unsupported exporter")

        exporter(database, arguments.output, github=github)


if __name__ == "__main__":
    arguments = parser.parse_args()
    main(arguments)
