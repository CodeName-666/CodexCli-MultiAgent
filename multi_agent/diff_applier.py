from __future__ import annotations

import abc
import fnmatch
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


class BaseDiffApplier(abc.ABC):
    @abc.abstractmethod
    def extract_diff(self, text: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def apply(
        self,
        workdir: Path,
        diff_text: str,
        diff_messages: Dict[str, str],
        diff_safety: Dict[str, object],
        diff_apply: Dict[str, object],
    ) -> Tuple[bool, str]:
        raise NotImplementedError


class UnifiedDiffApplier(BaseDiffApplier):
    DIFF_GIT_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)
    HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*$", re.MULTILINE)

    def extract_diff(self, text: str) -> str:
        """
        Extrahiert ab erstem 'diff --git ...' bis Ende.
        """
        m = self.DIFF_GIT_HEADER_RE.search(text or "")
        if not m:
            return ""
        return (text or "")[m.start():].strip()

    def apply(
        self,
        workdir: Path,
        diff_text: str,
        diff_messages: Dict[str, str],
        diff_safety: Dict[str, object],
        diff_apply: Dict[str, object],
    ) -> Tuple[bool, str]:
        """
        Sehr konservativer Unified-Diff Applier:
        - Erwartet git-style: diff --git a/... b/...
        - Erwartet, dass Kontextzeilen passen
        - Unterstützt Datei-Neuanlage, Änderungen, Löschungen (eingeschränkt)
        """
        try:
            safe, msg = self._check_safety(workdir, diff_text, diff_messages, diff_safety)
            if not safe:
                return False, msg
            if self._should_use_git(diff_apply, workdir):
                ok, msg = self._apply_with_git(workdir, diff_text, diff_messages, diff_apply)
                if ok:
                    return True, msg
                if diff_apply.get("fallback_to_builtin", True) is False:
                    return False, msg
            blocks = self._split_diff_by_file(diff_text, diff_messages)
            for rel_path, file_block in blocks:
                ok, msg = self._apply_file_block(workdir, rel_path, file_block, diff_messages)
                if not ok:
                    return False, msg
            return True, str(diff_messages["patch_applied"])
        except Exception as e:
            return False, str(diff_messages["patch_exception"]).format(error=e)

    def _check_safety(
        self,
        workdir: Path,
        diff_text: str,
        diff_messages: Dict[str, str],
        diff_safety: Dict[str, object],
    ) -> Tuple[bool, str]:
        blocklist = [str(item) for item in diff_safety.get("blocklist", [])]
        allowlist = [str(item) for item in diff_safety.get("allowlist", [])]
        if not blocklist:
            return True, ""
        paths = [m.group(2) for m in self.DIFF_GIT_HEADER_RE.finditer(diff_text)]
        for rel_path in paths:
            rel_path_norm = rel_path.replace("\\", "/")
            abs_path = (workdir / rel_path).resolve().as_posix()
            if self._is_allowed(rel_path_norm, abs_path, allowlist):
                continue
            if self._is_blocked(rel_path_norm, abs_path, blocklist):
                return False, str(diff_messages["blocked_path"]).format(path=rel_path_norm)
        return True, ""

    @staticmethod
    def _is_allowed(rel_path: str, abs_path: str, allowlist: List[str]) -> bool:
        for pattern in allowlist:
            pattern = str(Path(pattern).expanduser()).replace("\\", "/")
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(abs_path, pattern):
                return True
        return False

    @staticmethod
    def _is_blocked(rel_path: str, abs_path: str, blocklist: List[str]) -> bool:
        for pattern in blocklist:
            pattern = str(Path(pattern).expanduser()).replace("\\", "/")
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(abs_path, pattern):
                return True
        return False

    @staticmethod
    def _should_use_git(diff_apply: Dict[str, object], workdir: Path) -> bool:
        if not diff_apply.get("use_git", True):
            return False
        if not (workdir / ".git").exists():
            return False
        return shutil.which("git") is not None

    def _apply_with_git(
        self,
        workdir: Path,
        diff_text: str,
        diff_messages: Dict[str, str],
        diff_apply: Dict[str, object],
    ) -> Tuple[bool, str]:
        check = subprocess.run(
            ["git", "apply", "--check", "-"],
            input=diff_text,
            text=True,
            cwd=str(workdir),
            capture_output=True,
        )
        if check.returncode != 0:
            reason = (check.stderr or check.stdout or "").strip()
            return False, str(diff_messages["git_apply_check_failed"]).format(error=reason)
        apply = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", "-"],
            input=diff_text,
            text=True,
            cwd=str(workdir),
            capture_output=True,
        )
        if apply.returncode == 0:
            return True, str(diff_messages["patch_applied"])
        if diff_apply.get("use_3way", True):
            apply_3way = subprocess.run(
                ["git", "apply", "--3way", "-"],
                input=diff_text,
                text=True,
                cwd=str(workdir),
                capture_output=True,
            )
            if apply_3way.returncode == 0:
                return True, str(diff_messages["patch_applied_3way"])
            reason = (apply_3way.stderr or apply_3way.stdout or "").strip()
            return False, str(diff_messages["git_apply_failed"]).format(error=reason)
        reason = (apply.stderr or apply.stdout or "").strip()
        return False, str(diff_messages["git_apply_failed"]).format(error=reason)

    def _split_diff_by_file(self, diff_text: str, diff_messages: Dict[str, str]) -> List[Tuple[str, str]]:
        matches = list(self.DIFF_GIT_HEADER_RE.finditer(diff_text))
        if not matches:
            raise ValueError(str(diff_messages["no_git_header"]))
        blocks: List[Tuple[str, str]] = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(diff_text)
            block = diff_text[start:end].strip("\n")
            b_path = m.group(2)
            blocks.append((b_path, block))
        return blocks

    def _parse_old_new_paths(self, file_block: str) -> Tuple[str, str]:
        # sucht --- a/... und +++ b/...
        old = ""
        new = ""
        for line in file_block.splitlines():
            if line.startswith("--- "):
                old = line[4:].strip()
            elif line.startswith("+++ "):
                new = line[4:].strip()
            if old and new:
                break
        return old, new

    def _apply_file_block(
        self,
        workdir: Path,
        rel_path: str,
        file_block: str,
        diff_messages: Dict[str, str],
    ) -> Tuple[bool, str]:
        target = workdir / rel_path

        old_marker, new_marker = self._parse_old_new_paths(file_block)
        # /dev/null handling
        is_new_file = old_marker.endswith("/dev/null")
        is_deleted = new_marker.endswith("/dev/null")

        original_lines: List[str]
        if target.exists() and target.is_file():
            original_lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        else:
            original_lines = []

        out = original_lines[:]

        hunks = list(self.HUNK_RE.finditer(file_block))
        if not hunks:
            # Kein Hunk: akzeptieren
            if is_deleted and target.exists():
                try:
                    target.unlink()
                except OSError as e:
                    return False, str(diff_messages["delete_file_error"]).format(rel_path=rel_path, error=e)
            return True, str(diff_messages["no_hunks"]).format(rel_path=rel_path)

        # spans für hunk content
        spans: List[Tuple[int, int]] = []
        for i, hm in enumerate(hunks):
            start = hm.end()
            end = hunks[i + 1].start() if i + 1 < len(hunks) else len(file_block)
            spans.append((start, end))

        line_offset = 0

        for hm, (hs, he) in zip(hunks, spans):
            new_start = int(hm.group(3))
            hunk_lines = file_block[hs:he].splitlines()

            pos = (new_start - 1) + line_offset
            check_pos = pos
            consumed_old = 0
            new_block: List[str] = []

            for hl in hunk_lines:
                if not hl:
                    prefix, text = " ", ""
                else:
                    prefix, text = hl[0], hl[1:] if len(hl) > 1 else ""

                if prefix == " ":
                    if check_pos >= len(out) or out[check_pos] != text:
                        got = out[check_pos] if check_pos < len(out) else "EOF"
                        return False, str(diff_messages["context_mismatch"]).format(
                            rel_path=rel_path,
                            line=check_pos + 1,
                            expected=text,
                            got=got,
                        )
                    new_block.append(text)
                    check_pos += 1
                    consumed_old += 1
                elif prefix == "-":
                    if check_pos >= len(out) or out[check_pos] != text:
                        got = out[check_pos] if check_pos < len(out) else "EOF"
                        return False, str(diff_messages["delete_mismatch"]).format(
                            rel_path=rel_path,
                            line=check_pos + 1,
                            expected=text,
                            got=got,
                        )
                    check_pos += 1
                    consumed_old += 1
                elif prefix == "+":
                    new_block.append(text)
                elif prefix == "\\":
                    # "\ No newline at end of file"
                    continue
                else:
                    return False, str(diff_messages["unknown_prefix"]).format(rel_path=rel_path, prefix=prefix)

            out[pos:pos + consumed_old] = new_block
            line_offset += (len(new_block) - consumed_old)

        # Apply results
        if is_deleted:
            # wenn Diff eine Löschung signalisiert, löschen wir (wenn existiert)
            if target.exists():
                try:
                    target.unlink()
                except OSError as e:
                    return False, str(diff_messages["delete_file_error"]).format(rel_path=rel_path, error=e)
            return True, str(diff_messages["file_deleted"]).format(rel_path=rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
        if is_new_file:
            return True, str(diff_messages["file_created"]).format(rel_path=rel_path)
        return True, str(diff_messages["file_updated"]).format(rel_path=rel_path)
