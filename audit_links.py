import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

HTML_GLOBS = ["*.html"]
TSX_GLOBS = ["*.tsx", "*.ts"]
CSS_GLOBS = ["*.css"]


def list_files(root: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pat in patterns:
        files.extend(root.rglob(pat))
    return sorted({p for p in files if p.is_file()})


HREF_SRC_RE = re.compile(r"""(?P<attr>\bhref|\bsrc)\s*=\s*["'](?P<val>[^"']+)["']""", re.I)
CSS_URL_RE = re.compile(r"""url\(\s*['"]?(?P<val>[^'")]+)['"]?\s*\)""", re.I)


def is_external(url: str) -> bool:
    u = url.strip()
    return (
        u.startswith("http://")
        or u.startswith("https://")
        or u.startswith("//")
        or u.startswith("mailto:")
        or u.startswith("tel:")
        or u.startswith("javascript:")
        or u.startswith("#")
    )


def split_path_parts(p: str) -> list[str]:
    p = p.strip()
    p = p.split("?", 1)[0].split("#", 1)[0]
    p = p.replace("\\", "/")
    p = re.sub(r"^\./", "", p)
    p = re.sub(r"^/+", "", p)
    raw = [part for part in p.split("/") if part not in ("", ".")]
    # Normalize ".." lexically (do not allow escaping above root)
    parts: list[str] = []
    for part in raw:
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return parts


def check_case_sensitive_path(root: Path, repo_rel: str) -> tuple[bool, str]:
    """
    Returns (ok, reason). ok=false when the path doesn't exist OR when
    a segment's case doesn't match the real directory entry.
    """
    parts = split_path_parts(repo_rel)
    cur = root
    for idx, part in enumerate(parts):
        if not cur.exists() or not cur.is_dir():
            return False, f"Parent missing before segment '{part}'"
        entries = {e.name: e for e in cur.iterdir()}
        if part in entries:
            cur = entries[part]
            continue
        # Case mismatch check (Cloudflare Pages runs on Linux)
        lower_map = {name.lower(): name for name in entries.keys()}
        if part.lower() in lower_map:
            real = lower_map[part.lower()]
            seg_path = "/".join(parts[: idx + 1])
            return False, f"Case mismatch at '{seg_path}' (repo has '{real}')"
        seg_path = "/".join(parts[: idx + 1])
        return False, f"Missing '{seg_path}'"
    return True, "OK"


def resolve_url_from_file(file_path: Path, url: str) -> str:
    """
    Resolve URL (href/src/url()) to a normalized repo-relative path string.
    - leading '/' => relative to ROOT
    - otherwise => relative to the referencing file's directory
    """
    u = url.strip().split("?", 1)[0].split("#", 1)[0].replace("\\", "/")
    if u.startswith("/"):
        return u.lstrip("/")
    base_rel = file_path.parent.relative_to(ROOT).as_posix()
    joined = f"{base_rel}/{u}" if base_rel else u
    return "/".join(split_path_parts(joined))


def main() -> int:
    html_files = [p for p in list_files(ROOT, HTML_GLOBS) if p.parent == ROOT]
    tsx_files = [p for p in list_files(ROOT, TSX_GLOBS) if p.parent == ROOT]
    css_files = list_files(ROOT / "assets", CSS_GLOBS)

    findings: list[str] = []
    html_id_cache: dict[Path, set[str]] = {}

    def get_html_ids(fp: Path) -> set[str]:
        if fp in html_id_cache:
            return html_id_cache[fp]
        text = fp.read_text(encoding="utf-8", errors="replace")
        ids = set(re.findall(r"""\bid\s*=\s*["']([^"']+)["']""", text, flags=re.I))
        names = set(re.findall(r"""\bname\s*=\s*["']([^"']+)["']""", text, flags=re.I))
        html_id_cache[fp] = ids | names
        return html_id_cache[fp]

    # HTML/TSX href/src
    for fp in html_files + tsx_files:
        text = fp.read_text(encoding="utf-8", errors="replace")
        for m in HREF_SRC_RE.finditer(text):
            val = m.group("val").strip()
            if is_external(val):
                continue
            repo_rel = resolve_url_from_file(fp, val)
            ok, reason = check_case_sensitive_path(ROOT, repo_rel)
            if not ok:
                findings.append(f"[PATH] {fp.name}: {m.group('attr')}='{val}' -> {reason}")

            if m.group("attr").lower() == "href":
                raw = val.split("?", 1)[0]
                url, hash_part = (raw.split("#", 1) + [""])[:2]
                if url == "" and hash_part:
                    if fp.suffix.lower() == ".html":
                        ids = get_html_ids(fp)
                        if hash_part not in ids:
                            findings.append(f"[ANCHOR] {fp.name}: href='#{hash_part}' -> missing id/name '{hash_part}'")
                    continue

                if url.endswith(".html") or url == "/":
                    target = ROOT / ("index.html" if url == "/" else url.lstrip("/"))
                    if not target.exists():
                        findings.append(f"[LINK] {fp.name}: href='{val}' -> missing target '{target.name}'")
                    elif hash_part:
                        ids = get_html_ids(target)
                        if hash_part not in ids:
                            findings.append(
                                f"[ANCHOR] {fp.name}: href='{val}' -> target '{target.name}' missing id/name '{hash_part}'"
                            )

    # CSS url()
    for fp in css_files:
        text = fp.read_text(encoding="utf-8", errors="replace")
        for m in CSS_URL_RE.finditer(text):
            val = m.group("val").strip()
            if is_external(val) or val.startswith("data:"):
                continue
            repo_rel = resolve_url_from_file(fp, val)
            ok, reason = check_case_sensitive_path(ROOT, repo_rel)
            if not ok:
                findings.append(f"[CSS] {fp.relative_to(ROOT)}: url('{val}') -> {reason}")

    if not findings:
        print("OK: No broken/unsafe paths or missing internal links found.")
        return 0

    print("FINDINGS:")
    for line in sorted(set(findings)):
        print(" - " + line)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

