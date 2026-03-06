#!/usr/bin/env bash
# run-reviews.sh — Run Gemini and Codex code reviews in parallel.
#
# Usage: ./scripts/run-reviews.sh <review-doc-gemini> <review-doc-codex>
#
# The review docs contain instructions and a list of files to review.
# Each reviewer reads files directly from the repo using their own tools.
# Findings are written to .findings.md files alongside the review docs.
#
# SAFETY:
#   - Gemini: restricted to read-only tools (read_file, grep_search, glob, list_directory)
#   - Codex: runs in read-only sandbox (-s read-only)
#   Neither reviewer can modify any files in the repository.

set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <gemini-review.md> <codex-review.md>"
    echo ""
    echo "Example:"
    echo "  $0 docs/build/stage-5/gemini-review-impl.md docs/build/stage-5/codex-review-impl.md"
    exit 1
fi

GEMINI_DOC="$1"
CODEX_DOC="$2"
GEMINI_OUT="${GEMINI_DOC%.md}.findings.md"
CODEX_OUT="${CODEX_DOC%.md}.findings.md"

for f in "$GEMINI_DOC" "$CODEX_DOC"; do
    if [[ ! -f "$f" ]]; then
        echo "Error: $f not found"
        exit 1
    fi
done

SUFFIX="

IMPORTANT: You are running in the lit-explorer repository. Read ALL files listed in the review instructions above using your file reading tools. Then write your complete review findings in the format specified (### [SEVERITY] Title blocks). Output ONLY the findings — no preamble, no instructions echo. Do NOT modify any files."

echo "=== Starting parallel reviews ==="
echo "  Gemini: $GEMINI_DOC → $GEMINI_OUT"
echo "  Codex:  $CODEX_DOC → $CODEX_OUT"
echo ""

# Gemini: read-only via --allowed-tools whitelist, prompt via stdin
# The -p "" flag enables headless mode; actual prompt comes from stdin.
GEMINI_SAFE_TOOLS=(read_file grep_search glob list_directory google_web_search)

echo "  [Gemini] Starting (read-only: ${GEMINI_SAFE_TOOLS[*]})..."
{
    cat "$GEMINI_DOC"
    echo "$SUFFIX"
} | npx gemini -p "" --allowed-tools "${GEMINI_SAFE_TOOLS[@]}" > "$GEMINI_OUT" 2>&1 &
GEMINI_PID=$!

# Codex: read-only via sandbox, output captured via -o flag
echo "  [Codex]  Starting (sandbox: read-only)..."
CODEX_PROMPT="$(cat "$CODEX_DOC")$SUFFIX"
npx codex exec "$CODEX_PROMPT" -s read-only -o "$CODEX_OUT" > /dev/null 2>&1 &
CODEX_PID=$!

echo ""
echo "  Waiting for both reviewers..."

GEMINI_EXIT=0
CODEX_EXIT=0
wait $GEMINI_PID || GEMINI_EXIT=$?
wait $CODEX_PID || CODEX_EXIT=$?

echo ""
echo "=== Reviews complete ==="
echo "  Gemini: exit $GEMINI_EXIT → $GEMINI_OUT"
echo "  Codex:  exit $CODEX_EXIT → $CODEX_OUT"

# Show summary
for f in "$GEMINI_OUT" "$CODEX_OUT"; do
    if [[ -f "$f" ]]; then
        BLOCKERS=$(grep -c "^### \[BLOCKER\]" "$f" 2>/dev/null || true)
        CONCERNS=$(grep -c "^### \[CONCERN\]" "$f" 2>/dev/null || true)
        SUGGESTIONS=$(grep -c "^### \[SUGGESTION\]" "$f" 2>/dev/null || true)
        PRAISES=$(grep -c "^### \[PRAISE\]" "$f" 2>/dev/null || true)
        echo "  $(basename "$f"): ${BLOCKERS} blockers, ${CONCERNS} concerns, ${SUGGESTIONS} suggestions, ${PRAISES} praises"
    fi
done

echo ""
echo "To read findings:"
echo "  cat $GEMINI_OUT"
echo "  cat $CODEX_OUT"
