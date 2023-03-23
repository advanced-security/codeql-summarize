from codeqlsummarize.exporters.exptjson import exportToJson
from codeqlsummarize.exporters.customizations import exportBundle, exportCustomizations
from codeqlsummarize.exporters.extensions import exportDataExtensions

EXPORTERS = {
    "json": exportToJson,
    "extensions": exportDataExtensions,
    "customizations": exportCustomizations,
    "bundle": exportBundle,
}
