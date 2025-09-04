<!-- markdownlint-disable -->
<div align="center">

<h1>CodeQL Summarize</h1>

:warning: **This project is in early development and is not supported by GitHub or CodeQL** :warning:

[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/advanced-security/codeql-summarize)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/advanced-security/codeql-summarize/publish.yml?style=for-the-badge)](https://github.com/advanced-security/codeql-summarize/actions/workflows/publish.yml?query=branch%3Amain)
[![GitHub Issues](https://img.shields.io/github/issues/advanced-security/codeql-summarize?style=for-the-badge)](https://github.com/advanced-security/codeql-summarize/issues)
[![GitHub Stars](https://img.shields.io/github/stars/advanced-security/codeql-summarize?style=for-the-badge)](https://github.com/advanced-security/codeql-summarize)
[![License](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE)

</div>
<!-- markdownlint-restore -->


This is the GitHub CodeQL Summarize project and Actions which allows users to generate Models as Data (MaD) from CodeQL databases.

## Run

### Actions

The main use case for `codeqlsummarize` is to run it as an Action so the purposes of automating this process.

```yml
- name: Generate CodeQL Summaries
  uses: advanced-security/codeql-summarize@v1
  with:
    # This file defines the projects you want to make sure to get the latest and greatest
    # summaries from.
    projects: ./projects.json
    # Token needs access to download the CodeQL databases you want to create summaries for
    token: ${{ secrets.CODEQL_SUMMARY_GENERATOR_TOKEN }}
```

### GH CLI

You can install this tool as part of the GitHub CLI using the following commands:

```bash
gh extensions install advanced-security/gh-codeql-summarize
gh codeql-summarize --help
```

### Manual Command Line

```bash
git clone https://github.com/advanced-security/gh-codeql-summarize.git && cd gh-codeql-summarize
python3 -m codeqlsummarize --help
```

## License

This project is licensed under the terms of the MIT open source license. Please refer to [MIT](./LICENSE.txt) for the full terms.

## Maintainers 

[CODEOWNERS](./.github/CODEOWNERS) file.

## Support

Please create issues for any feature requests, bugs, or documentation problems.

## Acknowledgement

- @GeekMasher - Author
- @zbazztian - Major contributor
