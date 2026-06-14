from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from cl_legal_rag.parser import ParsedChunk, extract_chapter_title, split_by_articles


@dataclass(frozen=True)
class CommitInfo:
    """Metadatos principales de un commit de la constitucion."""

    sha: str
    date: str
    message: str


def _run_git(repo_path: Path, args: List[str]) -> str:
    """Ejecuta un comando git en un repo local y retorna stdout."""
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Error git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def list_master_commits(repo_path: Path) -> List[CommitInfo]:
    """Lista commits de master desde el mas antiguo al mas reciente."""
    log_format = "%H|%ad|%s"
    output = _run_git(
        repo_path,
        ["log", "--reverse", "--date=short", f"--pretty=format:{log_format}", "master"],
    )
    commits: List[CommitInfo] = []
    for line in output.splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        commits.append(CommitInfo(sha=parts[0], date=parts[1], message=parts[2]))
    return commits


def list_changed_markdown_files(repo_path: Path, sha: str) -> List[str]:
    """Obtiene archivos markdown modificados en un commit especifico."""
    output = _run_git(repo_path, ["show", "--pretty=format:", "--name-only", sha])
    files = [line.strip() for line in output.splitlines() if line.strip().endswith(".md")]
    return [
        f
        for f in files
        if f != "README.md" and ("Cap" in f or "Disposiciones" in f)
    ]


def show_file_at_commit(repo_path: Path, sha: str, file_path: str) -> str:
    """Obtiene contenido de archivo en un commit."""
    return _run_git(repo_path, ["show", f"{sha}:{file_path}"])


def _safe_ley(message: str) -> str:
    parts = message.strip().split()
    if len(parts) >= 2 and parts[0].upper() == "LEY":
        return f"LEY {parts[1]}"
    if len(parts) >= 3 and parts[0].upper() == "DECRETO" and parts[1].upper() == "LEY":
        return f"DECRETO LEY {parts[2]}"
    if len(parts) >= 2 and parts[0].upper() == "DECRETO":
        return f"DECRETO {parts[1]}"
    return message.strip()


def extract_history_chunks(repo_path: Path) -> List[ParsedChunk]:
    """Extrae chunks historicos solo de archivos tocados por cada commit."""
    commits = list_master_commits(repo_path)
    chunks: List[ParsedChunk] = []

    for commit in commits:
        changed_files = list_changed_markdown_files(repo_path, commit.sha)
        if not changed_files:
            continue

        for file_path in changed_files:
            try:
                text = show_file_at_commit(repo_path, commit.sha, file_path)
            except RuntimeError:
                continue

            chapter = extract_chapter_title(text, fallback=file_path)
            try:
                commit_chunks = split_by_articles(
                    markdown_text=text,
                    source="opensourcechile/constitucion_chile",
                    chapter=chapter,
                    chunk_prefix=f"hist_{commit.sha[:12]}",
                    extra_metadata={
                        "sha": commit.sha,
                        "commit_date": commit.date,
                        "ley": _safe_ley(commit.message),
                        "source_file": file_path,
                        "is_current": "false",
                    },
                )
            except ValueError:
                continue
            chunks.extend(commit_chunks)

    return chunks


def extract_current_chunks_from_repo(repo_path: Path) -> List[ParsedChunk]:
    """Extrae chunks del estado actual (HEAD/master) del repo raw."""
    files_output = _run_git(repo_path, ["ls-tree", "-r", "--name-only", "master"])
    chapter_files = [
        line.strip()
        for line in files_output.splitlines()
        if line.strip().endswith(".md") and line.strip() != "README.md"
    ]

    chunks: List[ParsedChunk] = []
    for file_path in chapter_files:
        text = show_file_at_commit(repo_path, "master", file_path)
        chapter = extract_chapter_title(text, fallback=file_path)
        try:
            file_chunks = split_by_articles(
                markdown_text=text,
                source="opensourcechile/constitucion_chile",
                chapter=chapter,
                chunk_prefix="current",
                extra_metadata={
                    "sha": "master",
                    "commit_date": "HEAD",
                    "ley": "vigente",
                    "source_file": file_path,
                    "is_current": "true",
                },
            )
        except ValueError:
            continue
        chunks.extend(file_chunks)

    return chunks
