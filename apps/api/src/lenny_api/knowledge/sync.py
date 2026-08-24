import subprocess
from pathlib import Path

from lenny_api.config import get_settings


class TranscriptSyncError(RuntimeError):
    pass


def run_git(arguments: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise TranscriptSyncError(detail)
    return result.stdout.strip()


def sync(repository_url: str, destination: Path) -> str:
    destination = destination.resolve()
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        run_git(["clone", "--depth", "1", repository_url, str(destination)])
    else:
        git_dir = destination / ".git"
        if not git_dir.is_dir():
            raise TranscriptSyncError(f"Refusing to overwrite non-Git directory: {destination}")
        origin = run_git(["remote", "get-url", "origin"], cwd=destination)
        normalized_origin = origin.removesuffix(".git").rstrip("/")
        normalized_expected = repository_url.removesuffix(".git").rstrip("/")
        if normalized_origin != normalized_expected:
            raise TranscriptSyncError(
                f"Existing checkout origin does not match configured repository: {origin}"
            )
        run_git(["pull", "--ff-only"], cwd=destination)
    return run_git(["rev-parse", "HEAD"], cwd=destination)


def main() -> None:
    settings = get_settings()
    commit = sync(settings.transcript_repository_url, Path(settings.transcript_source_dir))
    print(f"Transcript repository ready at commit {commit}")


if __name__ == "__main__":
    main()

