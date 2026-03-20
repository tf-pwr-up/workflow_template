#!/usr/bin/env python3
"""
council-dispatch.py — Mechanical API dispatch for council reviews.

Reads council-config.json for composition, dispatches review prompts to each
council member's configured platform in parallel, collects results, runs the
arbitrator, and produces a consolidated findings tracker.

Usage:
    ./scripts/council-dispatch.py <type> <sprint> "<title>"
    ./scripts/council-dispatch.py plan 1 "Sprint 1 plan review"
    ./scripts/council-dispatch.py analyze 0 "Initial requirements analysis"
    ./scripts/council-dispatch.py code 2 "Sprint 2 code review" --allow-external-code-review
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "council-config.json"

REVIEW_TYPES = ("analyze", "plan", "code")

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),                         # OpenAI / Anthropic keys
    re.compile(r"AIza[A-Za-z0-9_-]{35}"),                         # Google API keys
    re.compile(                                                     # Generic key=value secrets
        r"(api_key|secret|password|token|api_secret|private_key)"
        r"\s*[=:]\s*['\"]?[A-Za-z0-9_/+=\-]{8,}['\"]?",
        re.IGNORECASE,
    ),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-./+=]{20,}", re.IGNORECASE),  # Bearer tokens
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),                          # GitHub PATs
    re.compile(r"gho_[A-Za-z0-9]{36,}"),                          # GitHub OAuth tokens
    re.compile(r"xox[bpas]-[A-Za-z0-9\-]+"),                      # Slack tokens
]

MAX_ROUNDS = 5
QUORUM_MIN = 3
RETRY_ATTEMPTS = 2

# ---------------------------------------------------------------------------
# Helpers — API key sourcing
# ---------------------------------------------------------------------------


def _source_keys_from_profile() -> dict[str, str]:
    """Parse ~/.zprofile for exported env vars and return them as a dict."""
    profile = Path.home() / ".zprofile"
    found: dict[str, str] = {}
    if not profile.exists():
        return found
    try:
        with open(profile) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Match: export KEY=VALUE or export KEY="VALUE"
                m = re.match(
                    r"""^export\s+([A-Z_][A-Z0-9_]*)=["']?([^"'\s]+)["']?""",
                    line,
                )
                if m:
                    found[m.group(1)] = m.group(2)
    except OSError:
        pass
    return found


def ensure_api_keys_from_profile() -> None:
    """Ensure API keys are available in os.environ, falling back to ~/.zprofile."""
    needed = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    missing = [k for k in needed if not os.environ.get(k)]
    if not missing:
        return
    profile_vars = _source_keys_from_profile()
    for key in missing:
        if key in profile_vars:
            os.environ[key] = profile_vars[key]


# ---------------------------------------------------------------------------
# Helpers — Secret redaction
# ---------------------------------------------------------------------------


def redact_secrets(text: str) -> str:
    """Remove secret-shaped strings from text before sending to any API."""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


# ---------------------------------------------------------------------------
# Helpers — File reading
# ---------------------------------------------------------------------------


def read_file(path: Path) -> str:
    """Read a file and return its contents, or empty string on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"  Warning: could not read {path}: {exc}", file=sys.stderr)
        return ""


def read_glob(pattern: str) -> str:
    """Read all files matching a glob pattern relative to PROJECT_ROOT."""
    files = sorted(PROJECT_ROOT.glob(pattern))
    parts = []
    for f in files:
        content = read_file(f)
        if content:
            rel = f.relative_to(PROJECT_ROOT)
            parts.append(f"--- {rel} ---\n{content}")
    return "\n\n".join(parts)


def git_diff_for_sprint(sprint: int) -> str:
    """Return the git diff of changed files since the sprint base commit."""
    base_file = PROJECT_ROOT / f".sprint-base-commit-{sprint}"
    if base_file.exists():
        base_ref = base_file.read_text().strip()
    else:
        # Fall back to diffing against main
        base_ref = "main"

    try:
        result = subprocess.run(
            ["git", "diff", base_ref, "--", "."],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        # If diff is empty, try diffing staged + unstaged against HEAD
        result2 = subprocess.run(
            ["git", "diff", "HEAD", "--", "."],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )
        return result2.stdout if result2.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


# ---------------------------------------------------------------------------
# Material gathering
# ---------------------------------------------------------------------------


def gather_materials(review_type: str, sprint: int) -> str:
    """Gather the materials to be reviewed based on review type."""
    materials = []

    if review_type == "analyze":
        req_content = read_glob("docs/requirements/*.md")
        if req_content:
            materials.append(req_content)
        sprints_file = PROJECT_ROOT / "docs/requirements/proposed-sprints.md"
        if sprints_file.exists():
            materials.append(f"--- proposed-sprints.md ---\n{read_file(sprints_file)}")

    elif review_type == "plan":
        plan = PROJECT_ROOT / f"docs/plans/sprint-{sprint}-plan.md"
        gaps = PROJECT_ROOT / f"docs/gaps/sprint-{sprint}-gaps.md"
        if plan.exists():
            materials.append(f"--- Sprint {sprint} Plan ---\n{read_file(plan)}")
        if gaps.exists():
            materials.append(f"--- Sprint {sprint} Gaps ---\n{read_file(gaps)}")

    elif review_type == "code":
        diff = git_diff_for_sprint(sprint)
        if diff:
            materials.append(f"--- Git Diff (Sprint {sprint}) ---\n{diff}")
        plan = PROJECT_ROOT / f"docs/plans/sprint-{sprint}-plan.md"
        if plan.exists():
            materials.append(f"--- Sprint {sprint} Plan ---\n{read_file(plan)}")

    if not materials:
        print(f"Error: no materials found for {review_type} review (sprint {sprint})",
              file=sys.stderr)
        sys.exit(1)

    return "\n\n".join(materials)


# ---------------------------------------------------------------------------
# Round tracking
# ---------------------------------------------------------------------------


def get_round_number(review_type: str, sprint: int) -> int:
    """Get the current round number, incrementing the tracker file."""
    tracker = PROJECT_ROOT / f".review-round-sprint{sprint}-{review_type}"
    current = 0
    if tracker.exists():
        try:
            current = int(tracker.read_text().strip())
        except ValueError:
            current = 0
    new_round = current + 1
    tracker.write_text(str(new_round))
    return new_round


def record_base_commit(sprint: int) -> None:
    """Record the base commit for a sprint on first plan review."""
    base_file = PROJECT_ROOT / f".sprint-base-commit-{sprint}"
    if base_file.exists():
        return
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=10,
        )
        if result.returncode == 0:
            base_file.write_text(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def build_system_prompt(member: dict) -> str:
    """Build the system prompt for a council member."""
    role = member.get("role", "reviewer")
    lens = member.get("lens", "general quality and correctness")
    return (
        f"You are a {role} on a multi-model review council.\n"
        f"Your review lens: {lens}\n\n"
        f"Review the provided materials through your specific lens. Be thorough, "
        f"specific, and actionable. Reference specific sections, file paths, or "
        f"line numbers where applicable.\n\n"
        f"Categorise each finding as:\n"
        f"- **High**: Blocks approval. Must be addressed before proceeding.\n"
        f"- **Medium**: Should be addressed. May not block but degrades quality.\n"
        f"- **Low**: Suggestion for improvement. Nice to have.\n\n"
        f"At the end of your review, provide a verdict: APPROVED or CHANGES_REQUESTED.\n"
        f"If CHANGES_REQUESTED, list the specific changes needed."
    )


def build_arbitrator_prompt(member: dict, all_findings: list[dict]) -> str:
    """Build the system prompt for the arbitrator, including all other findings."""
    base = build_system_prompt(member)
    findings_text = "\n\n".join(
        f"### {f['role']} ({f['model']})\n{f['content']}"
        for f in all_findings
    )
    return (
        f"{base}\n\n"
        f"--- Previous Council Findings ---\n"
        f"You are the arbitrator. You have received the following findings from "
        f"other council members. Synthesise these into a final assessment. Resolve "
        f"any contradictions. Identify any gaps the other reviewers missed.\n\n"
        f"{findings_text}"
    )


def build_user_prompt(review_type: str, sprint: int, title: str,
                      materials: str, round_num: int) -> str:
    """Build the user prompt containing materials and output instructions."""
    return (
        f"# Council Review: Sprint {sprint} — {title} (Round {round_num})\n"
        f"Review type: {review_type}\n\n"
        f"## Materials for Review\n\n"
        f"{materials}\n\n"
        f"## Output Format\n\n"
        f"Structure your response as:\n\n"
        f"### Summary\n"
        f"Brief overall assessment (2-3 sentences).\n\n"
        f"### Findings\n"
        f"List each finding with severity (High/Medium/Low), description, and "
        f"recommended action.\n\n"
        f"### Verdict\n"
        f"APPROVED or CHANGES_REQUESTED\n\n"
        f"If CHANGES_REQUESTED, list the specific items that must be addressed."
    )


# ---------------------------------------------------------------------------
# Platform dispatch functions
# ---------------------------------------------------------------------------


def dispatch_codex(member: dict, system_prompt: str, user_prompt: str,
                   review_type: str) -> str:
    """Dispatch a review via Codex CLI."""
    model = member.get("model", "codex")

    if review_type == "code":
        # Use codex review for code reviews
        try:
            result = subprocess.run(
                ["codex", "review"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=300,
            )
            if result.returncode == 0:
                return result.stdout
            return f"Codex review failed (exit {result.returncode}): {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Codex review timed out after 300s"
        except FileNotFoundError:
            return "Error: codex CLI not found"

    # For plan/analyze — use codex exec with a temp file prompt
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, prefix="council-"
    ) as tf:
        tf.write(f"{system_prompt}\n\n---\n\n{user_prompt}")
        tf_path = tf.name

    try:
        result = subprocess.run(
            ["codex", "exec", "--full-auto", tf_path],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=300,
        )
        if result.returncode == 0:
            return result.stdout
        return f"Codex exec failed (exit {result.returncode}): {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Codex exec timed out after 300s"
    except FileNotFoundError:
        return "Error: codex CLI not found"
    finally:
        try:
            os.unlink(tf_path)
        except OSError:
            pass


def dispatch_gemini(member: dict, system_prompt: str, user_prompt: str) -> str:
    """Dispatch a review via Google Gemini API."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY not set"

    model = member.get("model", "gemini-2.5-pro")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n---\n\n{user_prompt}"}],
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8192,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        candidates = body.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)
        return f"Error: Gemini returned no candidates: {json.dumps(body)[:500]}"
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")[:500]
        return f"Error: Gemini HTTP {exc.code}: {error_body}"
    except Exception as exc:
        return f"Error: Gemini request failed: {exc}"


def dispatch_claude(member: dict, system_prompt: str, user_prompt: str) -> str:
    """Dispatch a review via Anthropic Claude API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not set"

    model = member.get("model", "claude-sonnet-4-20250514")
    url = "https://api.anthropic.com/v1/messages"

    payload = {
        "model": model,
        "max_tokens": 8192,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content_blocks = body.get("content", [])
        return "".join(
            block.get("text", "") for block in content_blocks if block.get("type") == "text"
        )
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")[:500]
        return f"Error: Claude HTTP {exc.code}: {error_body}"
    except Exception as exc:
        return f"Error: Claude request failed: {exc}"


def dispatch_openai(member: dict, system_prompt: str, user_prompt: str) -> str:
    """Dispatch a review via OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Error: OPENAI_API_KEY not set"

    model = member.get("model", "o3")
    url = "https://api.openai.com/v1/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 8192,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        choices = body.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return f"Error: OpenAI returned no choices: {json.dumps(body)[:500]}"
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")[:500]
        return f"Error: OpenAI HTTP {exc.code}: {error_body}"
    except Exception as exc:
        return f"Error: OpenAI request failed: {exc}"


# ---------------------------------------------------------------------------
# Unified dispatch with retry and fallback
# ---------------------------------------------------------------------------

PLATFORM_DISPATCHERS = {
    "codex": dispatch_codex,
    "gemini": dispatch_gemini,
    "claude": dispatch_claude,
    "openai": dispatch_openai,
}


def dispatch_member(
    member: dict,
    system_prompt: str,
    user_prompt: str,
    review_type: str,
) -> dict:
    """Dispatch a review to a single council member with retry and fallback."""
    role = member["role"]
    platform = member.get("platform", "claude")
    model = member.get("model", "unknown")
    fallback_platform = member.get("fallback_platform")
    fallback_model = member.get("fallback_model")

    dispatcher = PLATFORM_DISPATCHERS.get(platform)
    if not dispatcher:
        return {
            "role": role,
            "model": model,
            "platform": platform,
            "success": False,
            "content": f"Error: unknown platform '{platform}'",
        }

    # Retry on primary platform
    last_error = ""
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        if platform == "codex":
            content = dispatcher(member, system_prompt, user_prompt, review_type)
        else:
            content = dispatcher(member, system_prompt, user_prompt)

        if not content.startswith("Error:"):
            return {
                "role": role,
                "model": model,
                "platform": platform,
                "success": True,
                "content": content,
            }
        last_error = content
        if attempt < RETRY_ATTEMPTS:
            time.sleep(2 * attempt)  # Brief backoff

    # Try fallback if configured
    if fallback_platform and fallback_platform in PLATFORM_DISPATCHERS:
        fallback_member = {**member, "platform": fallback_platform}
        if fallback_model:
            fallback_member["model"] = fallback_model
        fallback_dispatcher = PLATFORM_DISPATCHERS[fallback_platform]

        if fallback_platform == "codex":
            content = fallback_dispatcher(fallback_member, system_prompt, user_prompt, review_type)
        else:
            content = fallback_dispatcher(fallback_member, system_prompt, user_prompt)

        if not content.startswith("Error:"):
            return {
                "role": role,
                "model": f"{fallback_model or model} (fallback)",
                "platform": fallback_platform,
                "success": True,
                "content": content,
            }
        last_error = content

    return {
        "role": role,
        "model": model,
        "platform": platform,
        "success": False,
        "content": last_error,
    }


# ---------------------------------------------------------------------------
# Results processing
# ---------------------------------------------------------------------------


def parse_verdict(content: str) -> str:
    """Extract verdict from review content."""
    # Look for explicit verdict markers
    if re.search(r"\bAPPROVED\b", content) and not re.search(r"\bCHANGES_REQUESTED\b", content):
        return "APPROVED"
    if re.search(r"\bCHANGES_REQUESTED\b", content):
        return "CHANGES_REQUESTED"
    return "UNCLEAR"


def count_findings(content: str) -> dict[str, int]:
    """Count findings by severity in review content."""
    return {
        "high": len(re.findall(r"\*\*High\*\*", content, re.IGNORECASE))
              + len(re.findall(r"(?:^|\n)\s*-\s*High\b", content, re.IGNORECASE)),
        "medium": len(re.findall(r"\*\*Medium\*\*", content, re.IGNORECASE))
                + len(re.findall(r"(?:^|\n)\s*-\s*Medium\b", content, re.IGNORECASE)),
        "low": len(re.findall(r"\*\*Low\*\*", content, re.IGNORECASE))
             + len(re.findall(r"(?:^|\n)\s*-\s*Low\b", content, re.IGNORECASE)),
    }


def consolidate_verdict(results: list[dict]) -> str:
    """Determine the consolidated verdict from all successful reviews."""
    verdicts = [parse_verdict(r["content"]) for r in results if r["success"]]
    if not verdicts:
        return "NO_REVIEWS"
    # Any CHANGES_REQUESTED blocks approval
    if any(v == "CHANGES_REQUESTED" for v in verdicts):
        return "CHANGES_REQUESTED"
    if all(v == "APPROVED" for v in verdicts):
        return "APPROVED"
    return "CHANGES_REQUESTED"  # Default to conservative if unclear


def consolidate_findings(results: list[dict]) -> dict[str, int]:
    """Sum findings across all successful reviews."""
    totals = {"high": 0, "medium": 0, "low": 0}
    for r in results:
        if r["success"]:
            counts = count_findings(r["content"])
            for key in totals:
                totals[key] += counts[key]
    return totals


# ---------------------------------------------------------------------------
# Output writing
# ---------------------------------------------------------------------------


def write_individual_reviews(
    results: list[dict], review_type: str, sprint: int, title: str, round_num: int
) -> Path:
    """Write individual review files and return the review directory."""
    if review_type == "analyze":
        review_dir = PROJECT_ROOT / "docs" / "reviews" / "analyze"
    else:
        review_dir = PROJECT_ROOT / "docs" / "reviews" / f"sprint-{sprint}"
    review_dir.mkdir(parents=True, exist_ok=True)

    for result in results:
        role_slug = re.sub(r"[^a-z0-9]+", "-", result["role"].lower()).strip("-")
        filepath = review_dir / f"{role_slug}.md"
        status = "Success" if result["success"] else "Failed"
        header = (
            f"# {result['role']} Review — {title} (R{round_num})\n\n"
            f"- **Model**: {result['model']}\n"
            f"- **Platform**: {result['platform']}\n"
            f"- **Status**: {status}\n"
            f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"---\n\n"
        )
        filepath.write_text(header + result["content"], encoding="utf-8")

    return review_dir


def write_findings_tracker(
    results: list[dict],
    review_type: str,
    sprint: int,
    title: str,
    round_num: int,
    verdict: str,
    findings: dict[str, int],
) -> Path:
    """Write or update the findings tracker file."""
    findings_dir = PROJECT_ROOT / "docs" / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)

    if review_type == "analyze":
        tracker_path = findings_dir / "analyze-findings.md"
    else:
        tracker_path = findings_dir / f"sprint-{sprint}-findings.md"

    successful = [r for r in results if r["success"]]
    total = len(results)
    success_count = len(successful)
    quorum_met = success_count >= QUORUM_MIN

    content = (
        f"# Council Findings: Sprint {sprint} — {title}\n\n"
        f"- **Review Type**: {review_type}\n"
        f"- **Round**: {round_num}\n"
        f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"- **Verdict**: {verdict}\n"
        f"- **Members**: {success_count} of {total} successful "
        f"(quorum: {'met' if quorum_met else 'NOT MET — minimum ' + str(QUORUM_MIN) + ' required'})\n"
        f"- **Findings**: {findings['high']} High, {findings['medium']} Medium, "
        f"{findings['low']} Low\n\n"
        f"---\n\n"
    )

    # Add per-member summary
    content += "## Member Verdicts\n\n"
    content += "| Role | Model | Platform | Verdict | High | Medium | Low |\n"
    content += "|------|-------|----------|---------|------|--------|-----|\n"
    for r in results:
        v = parse_verdict(r["content"]) if r["success"] else "FAILED"
        c = count_findings(r["content"]) if r["success"] else {"high": 0, "medium": 0, "low": 0}
        content += (
            f"| {r['role']} | {r['model']} | {r['platform']} | {v} "
            f"| {c['high']} | {c['medium']} | {c['low']} |\n"
        )

    content += "\n---\n\n"

    # Add individual findings detail
    content += "## Detailed Findings\n\n"
    for r in results:
        if r["success"]:
            content += f"### {r['role']} ({r['model']})\n\n{r['content']}\n\n---\n\n"

    # Convergence guardrails
    if round_num >= MAX_ROUNDS and verdict == "CHANGES_REQUESTED":
        content += (
            f"\n## Escalation Notice\n\n"
            f"This review has reached round {round_num} (maximum: {MAX_ROUNDS}) "
            f"without achieving APPROVED status. Manual intervention is required.\n"
            f"Remaining unresolved findings must be triaged by the project lead.\n"
        )

    tracker_path.write_text(content, encoding="utf-8")
    return tracker_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dispatch council reviews to configured multi-model reviewers.",
        epilog="Example: ./scripts/council-dispatch.py plan 1 'Sprint 1 plan review'",
    )
    parser.add_argument(
        "type",
        choices=REVIEW_TYPES,
        help="Review type: analyze, plan, or code",
    )
    parser.add_argument(
        "sprint",
        type=int,
        help="Sprint number (use 0 for analyze or ad-hoc reviews)",
    )
    parser.add_argument(
        "title",
        help="Descriptive title for the review",
    )
    parser.add_argument(
        "--allow-external-code-review",
        action="store_true",
        help="Required flag to confirm sending code to external APIs (for code reviews)",
    )
    args = parser.parse_args()

    # Validate: code reviews require explicit opt-in
    if args.type == "code" and not args.allow_external_code_review:
        print(
            "Error: Code reviews send source code to external APIs.\n"
            "Pass --allow-external-code-review to confirm this is intentional.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load config
    if not CONFIG_PATH.exists():
        print(f"Error: {CONFIG_PATH} not found.", file=sys.stderr)
        print("Create a council-config.json with your council composition.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(CONFIG_PATH) as fh:
            config = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Error: Failed to parse {CONFIG_PATH}: {exc}", file=sys.stderr)
        sys.exit(1)

    members = config.get("members", [])
    if not members:
        print("Error: No members defined in council-config.json.", file=sys.stderr)
        sys.exit(1)

    # Source API keys
    ensure_api_keys_from_profile()

    # Filter members by phase
    active_members = [
        m for m in members
        if args.type in m.get("phases", ["analyze", "plan", "code"])
    ]
    arbitrators = [m for m in active_members if m.get("arbitrator", False)]
    regular_members = [m for m in active_members if not m.get("arbitrator", False)]

    if not active_members:
        print(
            f"Error: No council members configured for '{args.type}' phase.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Record base commit on first plan review
    if args.type == "plan":
        record_base_commit(args.sprint)

    # Determine round
    round_num = get_round_number(args.type, args.sprint)

    # Convergence guardrail
    if round_num > MAX_ROUNDS:
        print(
            f"Error: Maximum review rounds ({MAX_ROUNDS}) exceeded for "
            f"sprint {args.sprint} {args.type} review.\n"
            f"Manual intervention required. Reset with: "
            f"rm {PROJECT_ROOT}/.review-round-sprint{args.sprint}-{args.type}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Gather and redact materials
    print(f"Gathering materials for {args.type} review...")
    materials = gather_materials(args.type, args.sprint)
    materials = redact_secrets(materials)

    # Build prompts
    user_prompt = build_user_prompt(args.type, args.sprint, args.title, materials, round_num)

    # Dispatch to regular members in parallel
    print(
        f"Dispatching to {len(regular_members)} council members "
        f"(+ {len(arbitrators)} arbitrator(s))..."
    )
    results: list[dict] = []

    with ThreadPoolExecutor(max_workers=min(len(regular_members), 6)) as executor:
        futures = {}
        for member in regular_members:
            sys_prompt = build_system_prompt(member)
            redacted_user_prompt = redact_secrets(user_prompt)
            future = executor.submit(
                dispatch_member, member, sys_prompt, redacted_user_prompt, args.type
            )
            futures[future] = member

        for future in as_completed(futures):
            member = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "role": member["role"],
                    "model": member.get("model", "unknown"),
                    "platform": member.get("platform", "unknown"),
                    "success": False,
                    "content": f"Error: Unexpected exception: {exc}",
                }
            status = "OK" if result["success"] else "FAILED"
            print(f"  {result['role']} ({result['platform']}): {status}")
            results.append(result)

    # Dispatch to arbitrator(s) with all findings
    successful_findings = [r for r in results if r["success"]]
    for arb in arbitrators:
        print(f"  Dispatching arbitrator: {arb['role']}...")
        arb_sys = build_arbitrator_prompt(arb, successful_findings)
        redacted_user_prompt = redact_secrets(user_prompt)
        arb_result = dispatch_member(arb, arb_sys, redacted_user_prompt, args.type)
        status = "OK" if arb_result["success"] else "FAILED"
        print(f"  {arb_result['role']} (arbitrator, {arb_result['platform']}): {status}")
        results.append(arb_result)

    # Check quorum
    successful_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    quorum_met = successful_count >= QUORUM_MIN

    if not quorum_met:
        print(
            f"\nWarning: Quorum not met. {successful_count} of {total_count} "
            f"reviews succeeded (minimum {QUORUM_MIN} required).",
            file=sys.stderr,
        )

    # Consolidate
    verdict = consolidate_verdict(results)
    findings = consolidate_findings(results)

    # Write outputs
    review_dir = write_individual_reviews(results, args.type, args.sprint, args.title, round_num)
    tracker_path = write_findings_tracker(
        results, args.type, args.sprint, args.title, round_num, verdict, findings
    )

    # Summary output
    print(f"\nCouncil Review: Sprint {args.sprint} - {args.title} (R{round_num})")
    print(f"Verdict: {verdict}")
    print(
        f"Members: {successful_count} of {total_count} successful "
        f"(quorum: {'met' if quorum_met else 'not met'})"
    )
    print(f"Findings: {findings['high']} High, {findings['medium']} Medium, {findings['low']} Low")
    print(f"Review written to: {review_dir.relative_to(PROJECT_ROOT)}/")
    print(f"Findings tracker: {tracker_path.relative_to(PROJECT_ROOT)}")

    if round_num >= MAX_ROUNDS and verdict == "CHANGES_REQUESTED":
        print(
            f"\nESCALATION: Round {round_num} of {MAX_ROUNDS} reached without approval. "
            f"Manual triage required."
        )

    # Exit with non-zero if not approved and quorum was met
    if verdict != "APPROVED" and quorum_met:
        sys.exit(2)
    elif not quorum_met:
        sys.exit(3)


if __name__ == "__main__":
    main()
