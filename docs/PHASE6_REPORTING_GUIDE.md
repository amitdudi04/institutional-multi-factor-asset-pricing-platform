# Phase 6 Reporting Guide

Reports are generated only from authenticated publication references. Supported formats are Markdown, escaped HTML, canonical JSON, and CSV metadata exports. Report requests select from a fixed section and format vocabulary; arbitrary template code and paths are rejected.

The report ID hashes template version, format, selected sections, software/configuration identity, publication identity, Git identity, and exact artifact checksums. The generation timestamp is deterministically derived from authenticated source creation times, or the Unix epoch for evidence without a creation time. This makes crash recovery and identical restart byte-stable.

Each report manifest records report ID, timestamp, source publications, artifact checksums, configuration identities, Git commits, software and template versions, limitations, disclaimer, output filename, and output checksum. Retrieval reauthenticates every source and compares the full artifact inventory before returning bytes. Changed sources or outputs fail closed.

Outputs remain inside `data/delivery/reports`, which is ignored runtime state. Safe filenames and resolved-path confinement reject traversal and symlink escape. Different existing content is never overwritten silently.
