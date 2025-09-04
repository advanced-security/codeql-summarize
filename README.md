<!-- markdownlint-disable -->
<div align="center">

<h1>CodeQL Summarize</h1>

:warning: <strong>Early project – not an official GitHub / CodeQL product</strong> :warning:

[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/advanced-security/codeql-summarize)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/advanced-security/codeql-summarize/publish.yml?style=for-the-badge)](https://github.com/advanced-security/codeql-summarize/actions/workflows/publish.yml?query=branch%3Amain)
[![GitHub Issues](https://img.shields.io/github/issues/advanced-security/codeql-summarize?style=for-the-badge)](https://github.com/advanced-security/codeql-summarize/issues)
[![GitHub Stars](https://img.shields.io/github/stars/advanced-security/codeql-summarize?style=for-the-badge)](https://github.com/advanced-security/codeql-summarize)
[![License](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE)

</div>
<!-- markdownlint-restore -->

Generate CodeQL Models-as-Data (MaD) summaries (sources, sinks, summaries) from existing CodeQL databases and export them in multiple formats suitable for:

- Data extensions (YAML) for CodeQL packs
- Customization libraries (`.qll`)
- Bundled packs containing generated customizations
- Raw JSON for further processing

## Key Features

- Automated download of CodeQL databases via the Code Scanning API (when a token is provided)
- Multiple export formats: `json`, `extensions`, `customizations`, `bundle`
- GitHub Action + GH CLI extension + direct CLI usage
- Automatic language detection from database metadata (fallback to manual selection)
- Caching support (skip with `--disable-cache`)
- Supports (current): `java`, `csharp`

## Supported Languages

Currently limited to the languages enforced in the code (`CODEQL_LANGUAGES`):

- Java
- C#

> Requests / PRs to add more languages are welcome once the upstream model generator queries support them.

## Quick Start

### 1. As a GitHub Action (recommended for automation)

```yml
- name: Generate CodeQL Summaries
  uses: advanced-security/codeql-summarize@v0.2.0
  with:
    projects: ./projects.json
    token: ${{ secrets.CODEQL_SUMMARY_GENERATOR_TOKEN }}
    format: extensions
    output: ./generated
```

### 2. GitHub CLI Extension

```bash
gh extension install advanced-security/gh-codeql-summarize
gh codeql-summarize --help
```

Example:

```bash
gh codeql-summarize \
  --format bundle \
  --input examples/projects.json \
  --output ./examples
```

### 3. Manual / Local CLI

```bash
git clone https://github.com/advanced-security/codeql-summarize.git
cd codeql-summarize
pipenv install --dev  # or pip install -e . if a setup is added later
pipenv run python -m codeqlsummarize --help
```

Minimal invocation (using a local database + explicit language):

```bash
python -m codeqlsummarize \
  -db /path/to/codeql-db \
  -l java \
  -f json \
  -o ./out
```

## Action Inputs

| Input        | Description                                                     | Default                    |
| ------------ | --------------------------------------------------------------- | -------------------------- |
| `project`    | Single repository (owner/name) to summarize                     | (none)                     |
| `projects`   | Path to a JSON file mapping language to list of repositories    | `./projects.json`          |
| `language`   | Comma-separated language list (overrides auto-detect)           | (auto)                     |
| `format`     | Export format: `json`, `extensions`, `customizations`, `bundle` | `extensions`               |
| `output`     | Output directory (or file for certain formats)                  | `./`                       |
| `repository` | GitHub repository context (fallback for `project`)              | `${{ github.repository }}` |
| `token`      | GitHub token used to download databases                         | `${{ github.token }}`      |

Notes:

- To download CodeQL databases the token must have appropriate permissions (typically `security_events:read` / `repo` depending on visibility). A fine‑grained PAT with Code scanning read access is recommended.
- If a database cannot be downloaded it will be skipped.

## Project File Schema (`projects.json`)

Example (`examples/projects.json`):

```json
{
  "java": ["ESAPI/esapi-java-legacy"]
}
```

Structure: `<language>` → array of `<owner>/<repo>` strings.

## Export Formats

| Format           | Description                                                             | Output Shape                                              |
| ---------------- | ----------------------------------------------------------------------- | --------------------------------------------------------- |
| `json`           | Raw rows per model type                                                 | One JSON file per database / summary (future enhancement) |
| `extensions`     | Data extensions YAML under a CodeQL pack structure                      | Writes `.yml` under `generated/` inside the detected pack |
| `customizations` | Single `.qll` customization library aggregating models                  | Requires `-o <file>.qll`                                  |
| `bundle`         | Initializes / updates a CodeQL pack containing generated customizations | Creates / updates pack in output dir                      |

`bundle` will (if necessary) create a pack (e.g. `java-summarize/`) and generate per‑repository `.qll` files plus a `Customizations.qll` aggregator.

## Environment Variables

| Variable            | Purpose                                  |
| ------------------- | ---------------------------------------- |
| `GITHUB_TOKEN`      | Default token for API calls (Actions)    |
| `GITHUB_REPOSITORY` | Default repo context (owner/name)        |
| `RUNNER_TEMP`       | Temp directory root (Actions)            |
| `DEBUG`             | If set (non-empty) enables debug logging |

## Exit / Error Behavior

The tool skips repositories whose databases cannot be fetched or located, logging warnings rather than stopping the entire run.

## Typical Workflow (Action + Extensions Format)

1. Maintain a `projects.json` file listing target repositories per language.
2. Schedule a workflow (e.g. nightly) to regenerate models.
3. Commit or publish the generated Data Extensions / Pack as needed.
4. Consume generated models in downstream CodeQL analysis.

## Development

Run tests:

```bash
pipenv run python -m unittest -v
```

Lint / format:

```bash
pipenv run black .
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Please open an issue before large changes.

## Security / Reporting Issues

See [SECURITY.md](./SECURITY.md).

## Support

See [SUPPORT.md](./SUPPORT.md). For general questions open a GitHub issue.

## Limitations / Roadmap

- Limited language set (Java, C#)
- No parallel download throttling handling yet
- No direct GitHub language detection fallback implemented
- JSON exporter minimal (subject to enhancement)

## License

Licensed under the MIT License – see [LICENSE](./LICENSE).

## Acknowledgements

- @GeekMasher – Author
- @zbazztian – Major contributor
