# Debugging with `aicontext debug`

The `debug` command helps you quickly assemble all relevant source files referenced in a stack trace and (optionally) export a ready-to-share context for AI assistance.

## Primary workflow

Pipe a stack trace to the command and provide the local project root used to resolve paths:

```bash
cat crash.log | aicontext debug from-trace --base-path /path/to/project
```

What happens:

- The tool scans the trace for file paths such as `/path/to/file.py:123`, `in /srv/app/file.php line 89`, or Windows-style paths like `C:\\project\\src\\main.ts:42`.
- It resolves those paths within the `--base-path` project.
- Resolved files are added to the session context stored in `~/.config/ai-context-manager/context.yaml`.
- Unresolved paths are reported.

## One-shot export

Write a combined debug context file (recommended: markdown) that includes the original stack trace at the top and the exported source content below:

```bash
cat crash.log | aicontext debug from-trace \
  --base-path /path/to/project \
  --output debug_context.md \
  --format markdown
```

- When `--format markdown` is used, the output begins with:
  - `# Debug Context`
  - `## Original Error Trace` followed by the provided stack trace in a fenced code block
  - The exported file contents and a directory tree
- For other formats (`json`, `xml`, `yaml`), the export is written as-is without the prepended trace.

## Options

- `--base-path, -b` (required): Local project root for resolving trace file paths.
- `--output, -o` (optional): Write the combined debug context to a file.
- `--format, -f` (optional): Export format (`markdown`, `json`, `xml`, `yaml`). The original trace is prepended only for markdown.

## Tips

- If your stack trace comes from a container or remote path, the command attempts to match by path suffix (e.g., `src/utils/file.py`). Ensure `--base-path` points to your local project root.
- The session context persists; you can later run `aicontext export` without specifying a profile to export the accumulated session files.
