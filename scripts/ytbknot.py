#!/usr/bin/env python3
"""
ytbknot.py — Single-call YouTube video data extractor for ytbknot.
Handles metadata, transcript, optional comments, and optional screenshots.
Returns structured markdown to stdout.

Usage:
    python ytbknot.py <URL> [--comments] [--screenshots [TIMESTAMPS]]
"""

from __future__ import annotations

import sys
import os
import re
import json
import glob
import subprocess
import tempfile
import argparse
import shutil
import datetime
from collections.abc import Sequence

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    os.environ["PYTHONUTF8"] = "1"

TMPDIR = tempfile.gettempdir()

# Semantic chunking defaults for long video analysis
DEFAULT_CHUNK_MINUTES = 15.0
CHUNK_MINUTES_BY_DETAIL = {
    "brief": 45.0,
    "standard": 15.0,
    "deep": 3.0,
}

# Visual grounding (--visual): how many evenly-spaced keyframes the summarizer
# worker looks at. Fixed (no override) — keeps the token cost predictable.
VISUAL_FRAME_COUNT = 4


def find_node_path() -> str | None:
    found = shutil.which("node")
    if found:
        return found
    candidates = [
        os.path.expanduser("~/.nvm/versions/node"),
        os.path.expanduser("~/.asdf/shims/node"),
        os.path.expanduser("~/.volta/bin/node"),
        os.path.expanduser("~/.fnm/current/bin/node"),
        "/usr/local/bin/node",
        "/usr/bin/node",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
        if os.path.isdir(c):
            try:
                subdirs = sorted(os.listdir(c), reverse=True)
                for s in subdirs:
                    p = os.path.join(c, s, "bin", "node")
                    if os.path.isfile(p) and os.access(p, os.X_OK):
                        return p
            except Exception:
                pass
    return None


def run_ytdlp(args: list[str]) -> subprocess.CompletedProcess:
    cmd = ["yt-dlp"]
    node_path = find_node_path()
    if node_path and os.path.exists(node_path):
        cmd.extend(["--js-runtimes", f"node:{node_path}"])
    cmd.extend(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )



# --- Utility functions ---


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    text = re.sub(r"-+", "-", text)
    return text[:max_length].rstrip("-")


def extract_video_id(url: str) -> str | None:
    """Extract the 11-char YouTube video ID from common URL forms
    (``watch?v=``, ``youtu.be/``, ``/shorts/``, ``/embed/``, ``/live/``).
    Returns None on no match. Used by --transcript-only mode to name the
    output folder without paying for a metadata fetch.
    """
    m = re.search(r"(?:v=|/shorts/|/embed/|/live/|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


CACHE_DIR = os.path.expanduser("~/.gemini/config/plugins/ytbknot/cache")


def get_cached_video(video_id: str) -> dict | None:
    path = os.path.join(CACHE_DIR, f"{video_id}.json")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_cached_video(video_id: str, data: dict) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{video_id}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def fetch_sponsorblock_segments(video_id: str) -> list[tuple[float, float]]:
    import urllib.request
    try:
        url = f"https://sponsor.ajay.app/api/skipSegments?videoID={video_id}&categories=[\"sponsor\",\"selfpromo\",\"interaction\",\"intro\",\"outro\"]"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            return [tuple(item["segment"]) for item in data if "segment" in item]
    except Exception:
        return []


def filter_sponsor_segments(segments: list[tuple[float, str]], sponsor_intervals: list[tuple[float, float]]) -> list[tuple[float, str]]:
    if not sponsor_intervals:
        return segments
    filtered = []
    for start, text in segments:
        is_sponsor = any(s_start <= start <= s_end for s_start, s_end in sponsor_intervals)
        if not is_sponsor:
            filtered.append((start, text))
    return filtered


def download_thumbnail(thumbnail_url: str, target_dir: str) -> str | None:
    if not thumbnail_url:
        return None
    import urllib.request
    try:
        target_path = os.path.join(target_dir, "thumbnail.jpg")
        req = urllib.request.Request(thumbnail_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            with open(target_path, "wb") as f:
                f.write(resp.read())
        return "thumbnail.jpg"
    except Exception:
        return None


def emit_stage(current: int, total: int, text: str) -> None:
    """Emit a progress stage marker on stderr, flushed immediately."""
    print(f"[{current}/{total}] {text}", file=sys.stderr, flush=True)


def strip_overlap(prev_text: str, next_text: str) -> str:
    """Return next_text with the longest word-prefix also present as word-suffix
    of prev_text stripped off. Used to collapse YouTube rolling-caption
    overlaps (each cue repeats the tail of the previous cue).

    Word-level comparison: 'Hello world' overlapping with 'world today' yields
    'today'. Idempotent for non-overlapping inputs (no strip, next_text returned
    verbatim).
    """
    prev_words = prev_text.split()
    next_words = next_text.split()
    max_k = min(len(prev_words), len(next_words))
    for k in range(max_k, 0, -1):
        if prev_words[-k:] == next_words[:k]:
            return " ".join(next_words[k:])
    return next_text


def format_timestamp_display(seconds: float) -> str:
    """Format seconds as M:SS or H:MM:SS for display."""
    s = int(seconds)
    h, remainder = divmod(s, 3600)
    m, sec = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def format_timestamp_filename(seconds: float) -> str:
    """Format seconds as MMmSSs or HhMMmSSs for filenames."""
    s = int(seconds)
    h, remainder = divmod(s, 3600)
    m, sec = divmod(remainder, 60)
    if h > 0:
        return f"{h}h{m:02d}m{sec:02d}s"
    return f"{m:02d}m{sec:02d}s"


def parse_timestamp(ts_str: str) -> float:
    """Parse user timestamp to seconds. Accepts: SS, M:SS, MM:SS, H:MM:SS, HH:MM:SS."""
    ts_str = ts_str.strip()
    if re.match(r"^\d+(\.\d+)?$", ts_str):
        return float(ts_str)
    parts = ts_str.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    raise ValueError(f"Invalid timestamp: {ts_str}")


def parse_vtt_timestamp(ts_str: str) -> float:
    """Parse VTT timestamp to seconds. Accepts HH:MM:SS.mmm and H:MM:SS.mmm."""
    match = re.match(r"(\d+):(\d{2}):(\d{2})\.(\d{3})", ts_str.strip())
    if match:
        h, m, s, ms = match.groups()
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    # Fallback: try without milliseconds
    match2 = re.match(r"(\d+):(\d{2}):(\d{2})", ts_str.strip())
    if match2:
        h, m, s = match2.groups()
        return int(h) * 3600 + int(m) * 60 + int(s)
    print(f"WARNING: Could not parse VTT timestamp: {ts_str}", file=sys.stderr)
    return 0.0


def format_date(upload_date: str) -> str:
    if len(upload_date) == 8:
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    return upload_date


def discover_categories(base_dir: str) -> list[str]:
    """Scan base_dir for existing non-hidden top-level category directories."""
    if not os.path.isdir(base_dir):
        return []
    ignored = {
        "screenshots", "cache", "rules", "scripts", "skills",
        "tests", "docs", "node_modules", "__pycache__", "venv",
        ".git", ".gemini", ".coding-friend", ".system_generated"
    }
    try:
        entries = sorted(os.listdir(base_dir))
        cats = [
            e for e in entries
            if os.path.isdir(os.path.join(base_dir, e))
            and not e.startswith(".")
            and e not in ignored
        ]
        return cats
    except OSError:
        return []


def render_metadata(meta: dict, category: str | None = None, detail_level: str = "standard") -> str:
    lines = [
        "### Metadata",
        f"title: {meta['title']}",
        f"channel: {meta['channel']}",
        f"date: {format_date(meta.get('upload_date', ''))}",
        f"duration: {meta.get('duration_string', '')}",
        f"duration_seconds: {meta.get('duration', 0)}",
        f"views: {meta.get('view_count', 0)}",
        f"likes: {meta.get('like_count', 0)}",
    ]
    if category:
        lines.append(f"category: {category}")
    lines.append(f"detail_level: {detail_level}")
    if meta.get("playlist_title"):
        lines.append(f"playlist: {meta['playlist_title']}")
    if meta.get("playlist_index"):
        lines.append(f"playlist_index: {meta['playlist_index']}")
    if meta.get("tags"):
        tags_str = ", ".join(meta["tags"][:8]) if isinstance(meta["tags"], list) else str(meta["tags"])
        lines.append(f"tags: [{tags_str}]")
    lines.extend([
        f"is_live: {meta.get('is_live', False)}",
        f"was_live: {meta.get('was_live', False)}",
        "",
    ])
    return "\n".join(lines)


def render_description(description: str) -> str:
    return "\n".join([
        "### Description",
        filter_description(description),
        "",
    ])


def render_chapters(chapters: list[dict]) -> str:
    if not chapters:
        return ""

    lines = ["### Chapters"]
    for ch in chapters:
        ts_display = format_timestamp_display(ch["start_time"])
        lines.append(f"- [{ts_display}] {ch['title']}")
    lines.append("")
    return "\n".join(lines)


def render_transcript_info(sub_hint: str, duration: float) -> str:
    lines = ["### Transcript Info", sub_hint]
    if duration and duration > 3600:
        lines.append(f"Video is {int(duration) // 60} min long — full transcript")
    lines.append("")
    return "\n".join(lines)


def render_transcript(
    transcript: str,
    segments: list[tuple[float, str]],
    screenshots: list[tuple[float, str]],
    chapters: list[dict],
) -> str:
    lines = ["### Transcript"]
    if transcript:
        if screenshots and segments:
            lines.append(embed_screenshots_in_transcript(segments, screenshots, chapters))
        else:
            lines.append(transcript)
    else:
        lines.append("No transcript available.")
    lines.append("")
    return "\n".join(lines)


def render_screenshots_section(
    screenshots_enabled: bool,
    screenshot_marker: str,
    screenshots: list[tuple[float, str]],
    chapters: list[dict],
    duration: float,
) -> str:
    if not screenshots_enabled:
        return ""

    lines = ["### Screenshots"]
    if screenshot_marker == "FFMPEG_MISSING":
        lines.append("FFMPEG_MISSING")
    elif screenshot_marker == "SCREENSHOTS_ASK_USER":
        lines.append("SCREENSHOTS_ASK_USER")
        lines.append(f"video_duration: {duration}")
    else:
        for ts, filename in screenshots:
            chapter_title = get_chapter_for_timestamp(ts, chapters)
            ts_display = format_timestamp_display(ts)
            rel_path = f"screenshots/{filename}"
            if chapter_title:
                lines.append(f"- ![{ts_display} — {chapter_title}]({rel_path}) {ts_display} — {chapter_title}")
            else:
                lines.append(f"- ![{ts_display}]({rel_path}) {ts_display}")
    lines.append("")
    return "\n".join(lines)


def render_screenshot_status(
    screenshots_enabled: bool,
    screenshot_marker: str,
    screenshot_requested: int,
    screenshots: list[tuple[float, str]],
    screenshot_warnings: list[str],
    deduped: int = 0,
) -> str:
    if not screenshots_enabled:
        return ""

    lines = ["### Screenshot Status"]
    if screenshot_marker:
        lines.append(screenshot_marker)
    elif screenshot_requested > 0:
        kept = len(screenshots)
        # "extracted" counts frames ffmpeg actually wrote (kept + deduped), so
        # perceptual dedup never looks like an extraction failure.
        extracted = kept + deduped
        line = f"{screenshot_requested} screenshots requested, {extracted} successfully extracted"
        if deduped:
            line += f", {deduped} near-duplicate(s) removed ({kept} kept)"
        lines.append(line + ".")
    for warning in screenshot_warnings:
        lines.append(f"- WARNING: {warning}")
    lines.append("")
    return "\n".join(lines)


def render_keyframes(tmpdir: str, frames: list[tuple[float, str]]) -> str:
    """Render the ### Keyframes section: one 'display_ts  abspath' line per
    extracted visual frame. The summarizer worker CONSUMES this section (Reads
    the images, weaves observations into the summary, deletes the temp dir) and
    strips it from its returned output — it is never relayed to the orchestrator.
    Returns "" when no frames were extracted (fail-open: summary is text-only)."""
    if not frames:
        return ""
    lines = ["### Keyframes"]
    for ts, fname in frames:
        path = os.path.join(tmpdir, fname).replace(os.sep, "/")
        lines.append(f"{format_timestamp_display(ts)}  {path}")
    lines.append("")
    return "\n".join(lines)


def render_comments(comments_requested: bool, comments: list[dict]) -> str:
    lines = ["### Comments"]
    if not comments_requested:
        lines.append("SKIPPED")
    elif comments:
        for i, c in enumerate(comments, 1):
            lines.append(f"{i}. **{c['author']}** (👍 {c['likes']}) — {c['text']}")
    else:
        lines.append("Comments not available.")
    return "\n".join(lines)


# --- Core extraction functions ---


def extract_metadata(url: str) -> dict | None:
    result = run_ytdlp(["--dump-json", "--no-playlist", "--no-warnings", url])
    if result.returncode != 0:
        return None
    try:
        d = json.loads(result.stdout)
        return {
            "id": d.get("id", ""),
            "title": d.get("title", ""),
            "channel": d.get("channel", ""),
            "upload_date": d.get("upload_date", ""),
            "duration_string": d.get("duration_string", ""),
            "duration": d.get("duration", 0),
            "view_count": d.get("view_count", 0),
            "like_count": d.get("like_count", 0),
            "description": d.get("description", ""),
            "is_live": d.get("is_live", False),
            "was_live": d.get("was_live", False),
            "chapters": d.get("chapters") or [],
            "thumbnail": d.get("thumbnail", ""),
            "playlist_title": d.get("playlist_title") or d.get("playlist") or "",
            "playlist_id": d.get("playlist_id") or "",
            "playlist_index": d.get("playlist_index"),
            "tags": d.get("tags") or [],
        }
    except (json.JSONDecodeError, KeyError):
        return None


def update_playlist_overview(pl_dir: str, meta: dict, category: str | None = None) -> None:
    """Create or update 00_overview.md in the playlist directory."""
    overview_path = os.path.join(pl_dir, "00_overview.md")
    pl_title = meta.get("playlist_title") or "Danh sách bài giảng"
    channel = meta.get("channel", "Không rõ")
    cat_str = category if category else "Chung"
    idx = meta.get("playlist_index")
    idx_str = f"{idx:02d}" if isinstance(idx, int) else "01"
    item_line = f"- [{idx_str}] {meta.get('title', '')}"

    if not os.path.isfile(overview_path):
        content = [
            f"# {pl_title}",
            "",
            f"* **Kênh:** {channel}",
            f"* **Danh mục:** {cat_str}",
            "",
            "---",
            "",
            "## Danh sách bài học",
            item_line,
            "",
        ]
        try:
            with open(overview_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
        except OSError:
            pass
    else:
        try:
            with open(overview_path, "r", encoding="utf-8") as f:
                existing = f.read()
            if meta.get("title") and meta["title"] not in existing:
                if "## Danh sách bài học" in existing:
                    updated = existing.rstrip() + f"\n{item_line}\n"
                else:
                    updated = existing.rstrip() + f"\n\n## Danh sách bài học\n{item_line}\n"
                with open(overview_path, "w", encoding="utf-8") as f:
                    f.write(updated)
        except OSError:
            pass


def download_and_process_vtt(url: str, video_id: str) -> tuple[str, str, list[tuple[float, str]]]:
    """Returns (transcript_text, subtitle_hint, segments).
    segments is a list of (start_seconds, text) tuples for timestamp mapping.
    """
    prefix = os.path.join(TMPDIR, f"yt_analyze_{video_id}")

    # Clean up any previous files for this ID
    for f in glob.glob(f"{prefix}*"):
        os.remove(f)

    result = run_ytdlp([
        "--write-auto-subs", "--write-subs",
        "--sub-langs", ".*orig,vi.*,en.*",
        "--sub-format", "vtt", "--convert-subs", "vtt",
        "--skip-download", "--no-playlist", "--no-warnings",
        "-o", f"{prefix}.%(ext)s",
        url,
    ])

    # Find VTT files
    vtt_files = glob.glob(f"{prefix}*.vtt")
    if not vtt_files:
        return "", "none", []

    vtt_path = vtt_files[0]
    filename = os.path.basename(vtt_path)

    # Auto-detection: check filename pattern only (yt-dlp marks auto-subs
    # in filenames; stderr contains "auto" in unrelated messages too)
    is_auto = ".auto." in filename.lower()

    # Extract language from filename pattern: yt_analyze_ID.LANG.vtt
    lang_match = re.search(r"\.([a-z]{2}(?:-[a-z]+)?(?:-orig)?)\.vtt$", filename, re.I)
    lang = lang_match.group(1) if lang_match else "en"

    # Process VTT to plain text AND timestamped segments
    with open(vtt_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    segments = []
    current_start = 0.0
    current_lines = []
    in_metadata_block = False  # NOTE/STYLE blocks span until next blank line

    for line in content.split("\n"):
        line = line.strip()

        # Blank line: end any open NOTE/STYLE block
        if not line:
            in_metadata_block = False
            continue
        # WebVTT header + file-level metadata fields
        if line.startswith("WEBVTT"):
            continue
        if re.match(r"^(Kind|Language):\s", line):
            continue
        # NOTE / STYLE blocks span lines until the next blank line
        if line.startswith("NOTE") or line.startswith("STYLE"):
            in_metadata_block = True
            continue
        if in_metadata_block:
            continue
        # Cue identifier lines (pure digits)
        if re.match(r"^\d+$", line):
            continue

        # Parse VTT timestamp lines: 00:02:15.000 --> 00:02:18.500
        arrow_match = re.match(
            r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}",
            line,
        )
        if arrow_match:
            # Save previous segment
            if current_lines:
                segments.append((current_start, " ".join(current_lines)))
            current_start = parse_vtt_timestamp(arrow_match.group(1))
            current_lines = []
            continue

        # Skip bare timestamp lines (without -->)
        if re.match(r"^\d{2}:\d{2}:\d{2}", line):
            continue

        # Text line — strip VTT tags
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if clean:
            current_lines.append(clean)

    # Don't forget the last segment
    if current_lines:
        segments.append((current_start, " ".join(current_lines)))

    # Cue-based rolling-overlap dedup.
    # YouTube auto-captions emit a 3-line rolling window where each cue repeats
    # the tail of the previous cue. The fix: for each new cue, strip the longest
    # word-prefix that matches the suffix of the already-accumulated text. One
    # pass catches both [A,B,C] -> [B,C,D] overlaps and fully-redundant cues.
    deduped_segments: list[tuple[float, str]] = []
    for start, text in segments:
        if not deduped_segments:
            deduped_segments.append((start, text))
            continue
        _, prev_text = deduped_segments[-1]
        stripped = strip_overlap(prev_text, text).strip()
        if stripped:
            deduped_segments.append((start, stripped))
        # else: this cue was entirely contained in the previous one — drop it.

    transcript = " ".join(text for _, text in deduped_segments).strip()

    # Cleanup temp files
    for f in glob.glob(f"{prefix}*"):
        os.remove(f)

    hint = f"auto-generated ({lang})" if is_auto else f"manual ({lang})"
    return transcript, hint, deduped_segments


def fetch_comments(url: str) -> list[dict]:
    result = run_ytdlp([
        "--write-comments",
        "--extractor-args", "youtube:comment_sort=top;max_comments=20,20,20,20",
        "--skip-download", "--dump-json",
        "--no-playlist", "--no-warnings",
        url,
    ])

    if result.returncode != 0:
        return []

    try:
        d = json.loads(result.stdout)
        comments = d.get("comments", [])
        comments.sort(key=lambda x: x.get("like_count", 0), reverse=True)
        return [
            {
                "author": c.get("author", ""),
                "likes": c.get("like_count", 0),
                "text": c.get("text", "")[:300],
            }
            for c in comments[:10]
        ]
    except (json.JSONDecodeError, KeyError):
        return []


def filter_description(desc: str) -> str:
    """Keep: tool links, GitHub repos, docs, chapter markers. Remove: social/subscribe/sponsor boilerplate."""
    lines = desc.split("\n")
    filtered = []
    skip_patterns = [
        r"(?i)(subscribe|follow\s+(me|us)|patreon|donation|sponsor|merch|social)",
        r"(?i)(instagram|twitter|x\.com|tiktok|facebook|discord\.gg|linkedin\.com/in/)",
    ]

    for line in lines:
        if any(re.search(p, line) for p in skip_patterns):
            continue
        filtered.append(line)

    return "\n".join(filtered).strip()


# --- Screenshot functions ---


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available in PATH."""
    return shutil.which("ffmpeg") is not None


def parse_screenshots_mode(arg: str) -> str:
    """Classify the --screenshots argument value.
    Returns 'interval', 'chapters', or 'timestamps'.
    """
    if arg in ("chapters", "auto"):
        return "chapters"
    if arg.startswith("interval="):
        return "interval"
    return "timestamps"


def chunk_transcript(
    segments: list[tuple[float, str]],
    duration: float,
    chunk_minutes: float = DEFAULT_CHUNK_MINUTES,
    chapters: list[dict] | None = None,
    detail_level: str = "standard",
) -> list[dict]:
    """Segment transcript into manageable semantic blocks for analysis.
    In 'brief' or 'standard' mode, if chapters are available (>= 3 chapters), use chapters.
    In 'deep' mode, if a chapter is longer than chunk_minutes, or if no chapters, subdivide into granular windows.
    Returns list of dicts:
        {'index': int, 'title': str, 'start': float, 'end': float, 'text': str, 'cues': list}
    """
    if not segments:
        return []

    chunks = []
    chunk_sec = chunk_minutes * 60.0

    # If chapters available with >= 3 items and not deep mode
    if chapters and len(chapters) >= 3 and detail_level != "deep":
        for idx, ch in enumerate(chapters, 1):
            ch_start = float(ch.get("start_time", 0.0))
            ch_end = _chapter_end_time(chapters, idx - 1)
            ch_title = ch.get("title", f"Khối {idx}").strip()
            ch_cues = [(t, txt) for t, txt in segments if ch_start <= t < ch_end]
            ch_text = " ".join(txt for _, txt in ch_cues).strip()
            chunks.append({
                "index": idx,
                "title": ch_title,
                "start": ch_start,
                "end": ch_end,
                "text": ch_text,
                "cues": ch_cues,
            })
        return chunks

    # Deep mode with chapters: subdivide chapters if they exceed chunk_sec, preserving chapter context
    if chapters and len(chapters) >= 3 and detail_level == "deep":
        idx = 1
        for ch_idx, ch in enumerate(chapters):
            ch_start = float(ch.get("start_time", 0.0))
            ch_end = _chapter_end_time(chapters, ch_idx)
            ch_title = ch.get("title", f"Phần {ch_idx+1}").strip()
            cur = ch_start
            sub_part = 1
            while cur < ch_end:
                nxt = min(ch_end, cur + chunk_sec)
                part_cues = [(t, txt) for t, txt in segments if cur <= t < nxt]
                part_text = " ".join(txt for _, txt in part_cues).strip()
                start_str = format_timestamp_display(cur)
                end_str = format_timestamp_display(nxt)
                suffix = f" (phần {sub_part})" if (ch_end - ch_start > chunk_sec) else ""
                chunks.append({
                    "index": idx,
                    "title": f"[{start_str} - {end_str}] {ch_title}{suffix}",
                    "start": cur,
                    "end": nxt,
                    "text": part_text,
                    "cues": part_cues,
                })
                idx += 1
                sub_part += 1
                cur = nxt
        return chunks

    # Otherwise chunk by time window (default 15m = 900s)
    chunk_sec = chunk_minutes * 60.0
    total_dur = duration if duration > 0 else (segments[-1][0] if segments else 0)
    current_start = 0.0
    idx = 1
    while current_start < total_dur:
        current_end = min(total_dur, current_start + chunk_sec)
        block_cues = [(t, txt) for t, txt in segments if current_start <= t < current_end]
        block_text = " ".join(txt for _, txt in block_cues).strip()
        start_str = format_timestamp_display(current_start)
        end_str = format_timestamp_display(current_end)
        chunks.append({
            "index": idx,
            "title": f"Khối {idx} ({start_str} - {end_str})",
            "start": current_start,
            "end": current_end,
            "text": block_text,
            "cues": block_cues,
        })
        current_start = current_end
        idx += 1

    return chunks


def render_transcript_chunks(chunks: list[dict]) -> str:
    """Render semantic chunks summary for structured Tier 2 analysis."""
    if not chunks:
        return ""
    lines = ["### Phân khối kịch bản (Semantic Chunks)"]
    for c in chunks:
        start_str = format_timestamp_display(c["start"])
        end_str = format_timestamp_display(c["end"])
        word_count = len(c["text"].split())
        lines.append(f"#### Khối {c['index']}: [{start_str} - {end_str}] — {c['title']} (~{word_count} từ)")
        excerpt = c["text"][:160] + "..." if len(c["text"]) > 160 else c["text"]
        lines.append(f"> Tóm lược đầu khối: {excerpt}\n")
    return "\n".join(lines).strip()





def get_chapter_for_timestamp(timestamp: float, chapters: list[dict]) -> str | None:
    """Find chapter title for a given timestamp."""
    for ch in chapters:
        if ch.get("start_time", 0) <= timestamp < ch.get("end_time", float("inf")):
            return ch.get("title", "")
    return None


def resolve_timestamps(
    screenshots_arg: str, chapters: list[dict], duration: float,
    warnings: list[str],
) -> list[float] | str:
    """Determine which timestamps to screenshot (chapters or explicit list).
    Returns list of seconds, or 'ASK_USER' if chapters mode but the video has
    no chapters. Scene mode never enters this function.
    Appends any issues to warnings list.
    """
    if screenshots_arg.startswith("interval="):
        try:
            interval_sec = float(screenshots_arg.split("=")[1])
            if interval_sec > 0 and duration > 0:
                count = int(duration // interval_sec)
                return [round(interval_sec * i, 1) for i in range(1, count + 1)]
        except ValueError:
            pass

    if screenshots_arg in ("chapters", "auto"):
        warnings.append(
            "Chapter-start captures often show intro/talking heads. "
            "Sampling within chapter body for active content."
        )
        if chapters:
            result = []
            for i, ch in enumerate(chapters):
                start = float(ch.get("start_time", 0))
                end = float(ch.get("end_time", duration)) if ch.get("end_time") is not None else (
                    float(chapters[i + 1]["start_time"]) if i + 1 < len(chapters) else duration
                )
                # Sample inside chapter body (40% mark, at least 15s in) to skip talking-head intro
                chap_len = max(0.0, end - start)
                offset = min(chap_len * 0.4, max(15.0, chap_len * 0.2)) if chap_len > 20 else chap_len * 0.5
                target_ts = round(start + offset, 1)
                if 0 <= target_ts <= duration:
                    result.append(target_ts)
            return result
        # Fallback when no chapters: distribute 8-12 evenly spaced frames
        if duration and duration > 0:
            count = min(12, max(6, int(duration // 180)))
            step = duration / (count + 1)
            return [round(step * i, 1) for i in range(1, count + 1)]
        return [0.0]

    # Parse comma-separated timestamps
    timestamps = []
    for ts in screenshots_arg.split(","):
        ts = ts.strip()
        if not ts:
            continue
        try:
            secs = parse_timestamp(ts)
            if 0 <= secs <= duration:
                timestamps.append(secs)
            else:
                msg = f"Timestamp {ts} ({secs}s) outside video duration ({duration}s), skipping."
                warnings.append(msg)
                print(f"WARNING: {msg}", file=sys.stderr)
        except ValueError as e:
            msg = f"{e}, skipping."
            warnings.append(msg)
            print(f"WARNING: {msg}", file=sys.stderr)

    return sorted(timestamps)


def get_stream_url(url: str) -> str | None:
    """Get direct video stream URL via yt-dlp -g (1080p Full HD quality)."""
    result = run_ytdlp([
        "-g", "-f", "bestvideo[height<=1080]/bestvideo/best",
        "--no-playlist", "--no-warnings", url,
    ])
    if result.returncode != 0:
        return None
    lines = result.stdout.strip().split("\n")
    return lines[0] if lines else None





def _long_path(path: str) -> str:
    """Return the \\\\?\\ extended-length form of an absolute Windows path.

    Windows' legacy 260-char MAX_PATH silently breaks os.path.exists()/
    getsize() for longer paths (observed with deep --output-base trees):
    ffmpeg writes the frame fine, but a plain stat() on the same path
    string returns False. The \\\\?\\ prefix opts into the real (32K) limit.
    No-op on non-Windows, where this limit does not exist.
    """
    if os.name != "nt":
        return path
    abspath = os.path.normpath(os.path.abspath(path))
    return abspath if abspath.startswith("\\\\?\\") else "\\\\?\\" + abspath


def extract_screenshots(
    url: str,
    timestamps: list[float],
    out_dir: str,
    chapters: list[dict],
    warnings: list[str],
) -> list[tuple[float, str]]:
    """Extract PNG screenshots at given timestamps via ffmpeg.
    Writes files directly into out_dir (caller owns that path).
    Returns [(timestamp_seconds, filename), ...] — filename is the basename
    only, so callers can build whatever relative path they need for markdown.
    Appends any issues to warnings list.
    """
    stream_url = get_stream_url(url)
    if not stream_url:
        msg = "Could not fetch stream URL. No screenshots extracted."
        warnings.append(msg)
        print(f"ERROR: {msg}", file=sys.stderr)
        return []

    os.makedirs(out_dir, exist_ok=True)

    results = []
    for i, ts in enumerate(timestamps, 1):
        chapter_title = get_chapter_for_timestamp(ts, chapters)
        ts_file = format_timestamp_filename(ts)

        if chapter_title:
            chapter_slug = slugify(chapter_title, 40)
            filename = f"{i:03d}_{ts_file}_{chapter_slug}.png"
        else:
            filename = f"{i:03d}_{ts_file}.png"

        filepath = os.path.join(out_dir, filename)

        # -y -loglevel BEFORE -ss; -ss BEFORE -i for fast input seeking.
        # Decimal seconds: truncating to int could seek BEFORE a detected
        # scene change and capture the previous screen.
        cmd = [
            "ffmpeg",
            "-y", "-loglevel", "error",
            "-ss", f"{ts:.2f}",
            "-i", stream_url,
            "-frames:v", "1",
            filepath,
        ]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            checked_path = _long_path(filepath)
            if os.path.exists(checked_path) and os.path.getsize(checked_path) > 0:
                results.append((ts, filename))
            else:
                err = proc.stderr.strip() if proc.stderr else "unknown error"
                msg = f"Frame at {format_timestamp_display(ts)} failed: {err}"
                warnings.append(msg)
                print(f"WARNING: {msg}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            msg = f"Frame at {format_timestamp_display(ts)} timed out (>60s)"
            warnings.append(msg)
            print(f"WARNING: {msg}", file=sys.stderr)

    return results





def _is_chapter_aligned(
    screenshots: list[tuple[float, str]],
    chapters: list[dict],
) -> bool:
    """True when there is exactly one screenshot per chapter and their
    timestamps line up within 1s. Used to pick the rendering strategy.
    """
    if not screenshots or not chapters or len(screenshots) != len(chapters):
        return False
    return all(
        abs(ss_ts - ch.get("start_time", -1)) < 1.0
        for (ss_ts, _), ch in zip(screenshots, chapters)
    )


def _chapter_end_time(chapters: list[dict], idx: int) -> float:
    """Return the end time for chapter idx — fall back to the next chapter's
    start, then to +∞ for the last chapter. yt-dlp usually supplies end_time,
    but this stays defensive in case it is missing.
    """
    ch = chapters[idx]
    end = ch.get("end_time")
    if end is not None:
        return float(end)
    if idx + 1 < len(chapters):
        return float(chapters[idx + 1].get("start_time", float("inf")))
    return float("inf")


def _render_chapter_structured(
    segments: list[tuple[float, str]],
    screenshots: list[tuple[float, str]],
    chapters: list[dict],
) -> str:
    """Transcript layout for chapter-aligned runs: one h3 block per chapter,
    screenshot right after the heading, then all transcript segments whose
    timestamp falls inside the chapter's interval.
    """
    parts: list[str] = []
    for i, chapter in enumerate(chapters):
        ch_start = float(chapter.get("start_time", 0.0))
        ch_end = _chapter_end_time(chapters, i)
        ch_title = chapter.get("title", "").strip()
        _, ss_filename = screenshots[i]
        ts_display = format_timestamp_display(ch_start)

        heading = f"### [{ts_display}] {ch_title}" if ch_title else f"### [{ts_display}]"
        alt = f"{ts_display} — {ch_title}" if ch_title else ts_display

        parts.append(f"\n\n{heading}\n\n")
        parts.append(f"![{alt}](screenshots/{ss_filename})\n\n")

        for seg_ts, seg_text in segments:
            if ch_start <= seg_ts < ch_end:
                parts.append(seg_text + " ")

    return "".join(parts).strip()


def _render_inline_with_heading(
    segments: list[tuple[float, str]],
    screenshots: list[tuple[float, str]],
    chapters: list[dict],
) -> str:
    """Fallback layout when the run is not chapter-aligned (custom timestamps,
    no chapters, or count mismatch). Each screenshot gets an h3 heading just
    before the image so readers see the timestamp context in full-transcript
    mode. If the timestamp happens to fall inside a chapter, the chapter title
    is appended to the heading after an em-dash.
    """
    if not segments:
        return ""

    screenshot_map: dict[int, list[str]] = {}
    for ts, filename in screenshots:
        best_idx = 0
        for idx, (seg_ts, _) in enumerate(segments):
            if seg_ts <= ts:
                best_idx = idx
            else:
                break

        chapter_title = get_chapter_for_timestamp(ts, chapters)
        ts_display = format_timestamp_display(ts)

        if chapter_title:
            heading = f"### [{ts_display}] — {chapter_title}"
            alt = f"{ts_display} — {chapter_title}"
        else:
            heading = f"### [{ts_display}]"
            alt = ts_display

        ref = f"\n\n{heading}\n\n![{alt}](screenshots/{filename})\n\n"
        screenshot_map.setdefault(best_idx, []).append(ref)

    parts: list[str] = []
    for idx, (_, text) in enumerate(segments):
        if idx in screenshot_map:
            for ref in screenshot_map[idx]:
                parts.append(ref)
        parts.append(text + " ")

    return "".join(parts).strip()


def embed_screenshots_in_transcript(
    segments: list[tuple[float, str]],
    screenshots: list[tuple[float, str]],
    chapters: list[dict],
) -> str:
    """Insert screenshots into the transcript. Picks between two layouts:

    - Chapter-structured (one screenshot per chapter, timestamps aligned):
      ``### [HH:MM] Chapter Title`` heading, image, segments of that chapter.
    - Inline-with-heading fallback (custom timestamps or mismatch): the
      existing inline insert, but each image is preceded by its own
      ``### [HH:MM]`` heading for scannability.

    screenshots is [(ts, filename), ...] — filenames resolved against the
    sibling ``screenshots/`` folder where the markdown will live.
    """
    if not segments:
        return ""

    if _is_chapter_aligned(screenshots, chapters):
        return _render_chapter_structured(segments, screenshots, chapters)
    return _render_inline_with_heading(segments, screenshots, chapters)


# --- Main ---


def run_transcript_only(args: argparse.Namespace) -> None:
    """Lean path: fetch and emit ONLY the raw transcript. No metadata fetch,
    no comments, no screenshots, no summary. Names the output folder by the
    video ID parsed from the URL (falls back to a URL-derived slug).
    """
    url = args.url
    total_stages = 2

    video_id = extract_video_id(url)
    slug = video_id or ("video-" + slugify(url, 40))

    date_str = datetime.date.today().isoformat()
    target = os.path.join(args.output_base, f"ytbknot_{date_str}_{slug}")

    # Collision guard before any work — so a re-run without --force does not
    # emit a stage marker for work it never starts.
    if os.path.isdir(target) and not args.force:
        print(f"FOLDER_EXISTS: {target}", file=sys.stderr, flush=True)
        sys.exit(2)
    os.makedirs(target, exist_ok=True)

    emit_stage(1, total_stages, "Downloading transcript")
    # Pass `slug` (not a fixed literal) as the temp-file discriminator so the
    # VTT temp prefix stays unique per video even when extract_video_id misses.
    transcript, sub_hint, segments = download_and_process_vtt(url, slug)

    emit_stage(2, total_stages, "Writing output")
    sections = [
        # duration is unknown in transcript-only mode (no metadata fetch), so
        # pass 0 — render_transcript_info deliberately omits the long-video hint.
        render_transcript_info(sub_hint, 0),
        render_transcript(transcript, segments, [], []),
    ]
    print("\n".join(section for section in sections if section))

    # Deliberate blank line: OUTPUT_FOLDER: must be the last non-empty stdout
    # line so the skill can parse it.
    print()
    print(f"OUTPUT_FOLDER: {target.replace(os.sep, '/')}")


def main():
    parser = argparse.ArgumentParser(description="Extract YouTube video data")
    parser.add_argument("url", help="YouTube URL")
    parser.add_argument("--comments", action="store_true", help="Also fetch top comments")
    parser.add_argument(
        "--screenshots", nargs="?", const="chapters", default=None,
        help="Extract screenshots. Comma-separated timestamps (0:30,2:15,5:00), "
             "'chapters', or omitted to skip (reconnaissance mode).",
    )
    parser.add_argument(
        "--no-screenshots", action="store_true",
        help="Disable automatic screenshot extraction",
    )
    parser.add_argument(
        "--interval", type=float, default=None,
        help="Extract screenshots every N seconds (e.g. --interval 60)",
    )
    parser.add_argument(
        "--output-base", default=".",
        help="Base directory for the output folder (default: current directory). "
             "Script creates '<base>/[category]/[playlist]/<slug>/' inside it.",
    )
    parser.add_argument(
        "--category", default=None,
        help="Category or subject domain for the lecture (e.g. 'toeic', 'system-design'). "
             "If specified, folder is placed under '<output-base>/<category>/'.",
    )
    parser.add_argument(
        "--detail", choices=["brief", "standard", "deep"], default="standard",
        help="Detail level: 'brief' (overview only), 'standard' (balanced 2-layer), "
             "'deep' (granular breakdown with micro-segments). Default: standard.",
    )
    parser.add_argument(
        "--playlist-title", default=None,
        help="Explicit playlist title for series organization.",
    )
    parser.add_argument(
        "--playlist-index", type=int, default=None,
        help="Explicit index/position of the video within the playlist.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing target folder. Without this flag the script "
             "exits with code 2 + 'FOLDER_EXISTS: <path>' on stderr when the "
             "target already exists.",
    )
    parser.add_argument(
        "--transcript-only", action="store_true",
        help="Fetch and output ONLY the raw transcript — no metadata, "
             "description, chapters, comments, or screenshots. Skips the "
             "metadata fetch; names the output folder by video ID.",
    )
    parser.add_argument(
        "--visual", action="store_true",
        help="Extract a few evenly-spaced keyframes to a temp dir and emit a "
             "### Keyframes section so the summarizer can address on-screen "
             "content. Ephemeral: the summarizer reads then deletes them.",
    )
    parser.add_argument(
        "--clean-ads", action="store_true",
        help="Filter out sponsor and self-promo segments via SponsorBlock API.",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Bypass local cache and force re-fetching all data from YouTube.",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Do not create target folder or save thumbnail; print output and cache only.",
    )
    args = parser.parse_args()

    if args.no_save:
        args.screenshots = None
    elif args.no_screenshots:
        args.screenshots = None
    elif args.interval:
        args.screenshots = f"interval={args.interval}"

    if args.transcript_only:
        run_transcript_only(args)
        return

    url = args.url
    video_id = extract_video_id(url)
    cached = get_cached_video(video_id) if (video_id and not args.refresh) else None

    # --- Screenshot warnings and stages ---
    screenshot_warnings: list[str] = []

    # --- Stage count (adaptive to enabled features) ---
    stages = ["metadata", "transcript"]
    if args.comments:
        stages.append("comments")
    if args.screenshots is not None:
        stages.append("screenshots")
    if args.visual:
        stages.append("visual")
    stages.append("output")
    total_stages = len(stages)
    stage_idx = 0

    # --- Step 1: Metadata ---
    stage_idx += 1
    if cached and "meta" in cached:
        emit_stage(stage_idx, total_stages, "Loading metadata from local cache")
        meta = cached["meta"]
    else:
        emit_stage(stage_idx, total_stages, "Fetching metadata")
        meta = extract_metadata(url)
        if not meta:
            print(f"ERROR: Could not fetch metadata for {url}")
            sys.exit(1)

    # --- Compute target folder hierarchy ---
    if args.playlist_title:
        meta["playlist_title"] = args.playlist_title
    if args.playlist_index is not None:
        meta["playlist_index"] = args.playlist_index

    cat_dir = os.path.join(args.output_base, slugify(args.category)) if args.category else args.output_base
    slug = slugify(meta["title"])
    pl_title = meta.get("playlist_title")

    if pl_title:
        pl_dir = os.path.join(cat_dir, slugify(pl_title))
        pl_idx = meta.get("playlist_index")
        prefix = f"{pl_idx:02d}_" if isinstance(pl_idx, int) else ""
        target = os.path.join(pl_dir, f"{prefix}{slug}")
    else:
        pl_dir = None
        target = os.path.join(cat_dir, slug)

    # --- Collision guard & Target folder creation ---
    if not args.no_save:
        if os.path.isdir(target) and not args.force:
            print(f"FOLDER_EXISTS: {target}", file=sys.stderr, flush=True)
            sys.exit(2)

        if pl_dir:
            os.makedirs(pl_dir, exist_ok=True)
            update_playlist_overview(pl_dir, meta, args.category)

        os.makedirs(target, exist_ok=True)

        # Download thumbnail if present
        if meta.get("thumbnail"):
            download_thumbnail(meta["thumbnail"], target)

    # --- Step 2: Transcript ---
    stage_idx += 1
    if cached and "transcript" in cached and "segments" in cached:
        emit_stage(stage_idx, total_stages, "Loading transcript from local cache")
        transcript = cached["transcript"]
        sub_hint = cached.get("sub_hint", "cached")
        segments = [tuple(s) for s in cached["segments"]]
    else:
        emit_stage(stage_idx, total_stages, "Downloading transcript")
        transcript, sub_hint, segments = download_and_process_vtt(url, meta["id"])
        if meta.get("id"):
            save_cached_video(meta["id"], {
                "meta": meta,
                "transcript": transcript,
                "sub_hint": sub_hint,
                "segments": segments,
            })

    # --- SponsorBlock filter (optional) ---
    if args.clean_ads and meta.get("id") and segments:
        sponsors = fetch_sponsorblock_segments(meta["id"])
        if sponsors:
            before_len = len(segments)
            segments = filter_sponsor_segments(segments, sponsors)
            transcript = " ".join(t for _, t in segments).strip()
            emit_stage(stage_idx, total_stages, f"Filtered {before_len - len(segments)} sponsor cues via SponsorBlock")

    # --- Step 3: Comments (optional) ---
    comments = []
    if args.comments:
        stage_idx += 1
        emit_stage(stage_idx, total_stages, "Fetching comments")
        comments = fetch_comments(url)

    # --- Step 4: Screenshots (optional) ---
    screenshots = []
    screenshot_requested = 0
    screenshot_marker = ""  # "FFMPEG_MISSING" or "SCREENSHOTS_ASK_USER"
    if args.screenshots is not None:
        if not check_ffmpeg():
            stage_idx += 1
            screenshot_marker = "FFMPEG_MISSING"
            screenshot_warnings.append("ffmpeg not found — no screenshots extracted.")
            emit_stage(stage_idx, total_stages, "Screenshots skipped (ffmpeg missing)")
        else:
            timestamps = resolve_timestamps(
                args.screenshots, meta["chapters"], meta["duration"],
                screenshot_warnings,
            )
            stage_idx += 1
            if timestamps == "ASK_USER":
                screenshot_marker = "SCREENSHOTS_ASK_USER"
                emit_stage(stage_idx, total_stages, "Screenshots deferred (no chapters)")
            elif timestamps:
                screenshot_requested = len(timestamps)
                emit_stage(
                    stage_idx, total_stages,
                    f"Extracting {screenshot_requested} screenshots",
                )
                out_dir = os.path.join(target, "screenshots")
                screenshots = extract_screenshots(
                    url, timestamps, out_dir, meta["chapters"],
                    screenshot_warnings,
                )
            else:
                emit_stage(stage_idx, total_stages, "No valid screenshot timestamps")

    # --- Step 4b: Visual keyframes (optional, ephemeral) ---
    visual_frames: list[tuple[float, str]] = []
    visual_tmpdir = ""
    if args.visual:
        stage_idx += 1
        if not check_ffmpeg():
            emit_stage(stage_idx, total_stages, "Visual keyframes skipped (ffmpeg missing)")
        else:
            emit_stage(
                stage_idx, total_stages,
                f"Extracting {VISUAL_FRAME_COUNT} keyframes for visual grounding",
            )
            vts = evenly_spaced_timestamps(meta["duration"], VISUAL_FRAME_COUNT)
            if vts:
                visual_tmpdir = tempfile.mkdtemp(prefix="ytbknot-visual-")
                visual_frames = extract_screenshots(url, vts, visual_tmpdir, [], [])
                if not visual_frames:
                    shutil.rmtree(visual_tmpdir, ignore_errors=True)
                    visual_tmpdir = ""

    # --- Step 5: Output ---
    stage_idx += 1
    emit_stage(stage_idx, total_stages, "Writing output")

    # --- Output structured markdown ---
    chunk_min = CHUNK_MINUTES_BY_DETAIL.get(args.detail, DEFAULT_CHUNK_MINUTES)
    chunks = chunk_transcript(
        segments,
        meta["duration"],
        chunk_minutes=chunk_min,
        chapters=meta["chapters"],
        detail_level=args.detail,
    )
    sections = [
        render_metadata(meta, args.category, detail_level=args.detail),
        render_description(meta["description"]),
        render_chapters(meta["chapters"]),
        render_transcript_chunks(chunks),
        render_transcript_info(sub_hint, meta["duration"]),
        render_transcript(transcript, segments, screenshots, meta["chapters"]),
        render_screenshots_section(
            args.screenshots is not None,
            screenshot_marker,
            screenshots,
            meta["chapters"],
            meta["duration"],
        ),
        render_screenshot_status(
            args.screenshots is not None,
            screenshot_marker,
            screenshot_requested,
            screenshots,
            screenshot_warnings,
            deduped=0,
        ),
        render_keyframes(visual_tmpdir, visual_frames),
        render_comments(args.comments, comments),
    ]
    print("\n".join(section for section in sections if section))

    # --- Trailer: tell the orchestrator where the output folder lives ---
    # Forward slashes so the marker is stable across platforms — the skill
    # parses this line verbatim to decide where to write the MD file.
    print()
    if args.no_save:
        print(f"OUTPUT_FOLDER: NONE (recon mode, cached {meta.get('id', '')})")
        existing_cats = discover_categories(args.output_base)
        if existing_cats:
            print(f"EXISTING_CATEGORIES: {', '.join(existing_cats)}")
        else:
            print("EXISTING_CATEGORIES: NONE")
    else:
        print(f"OUTPUT_FOLDER: {target.replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
