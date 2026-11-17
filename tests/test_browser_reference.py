"""The generated browser command reference stays current and separate.

The `browser` commands are documented in their own generated file beside
reference.md, so their flags never add to the SKILL.md + reference.md budget
that `test_context_cost_claim.py` measures. This applies the staleness check of
`test_skill_reference_current.py` to that file.
"""

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "src" / "zotero_mcp" / "skills" / "zotero-cli"
BROWSER_REFERENCE = SKILL_DIR / "browser-reference.md"
GENERATOR = REPO / "scripts" / "gen_skill_reference.py"


def _generator():
    spec = importlib.util.spec_from_file_location("gen_skill_reference", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _browser_parsers() -> dict[str, argparse.ArgumentParser]:
    from zotero_mcp.cli_standalone import build_parser

    def subcommands(parser):
        action = next(a for a in parser._actions
                      if isinstance(a, argparse._SubParsersAction))
        return action.choices

    return dict(subcommands(subcommands(build_parser())["browser"]))


class TestBrowserReference:
    def test_matches_the_current_parser(self):
        """If this fails, run `python scripts/gen_skill_reference.py`."""
        assert BROWSER_REFERENCE.read_text(encoding="utf-8") == \
            _generator().build_separate("browser"), (
                "browser-reference.md is stale -- run "
                "`python scripts/gen_skill_reference.py` and commit the result."
            )

    def test_is_split_out_of_the_main_reference(self):
        """Listing browser flags in reference.md too would spend the context
        budget the split exists to protect."""
        assert "`browser" not in (SKILL_DIR / "reference.md").read_text(encoding="utf-8")
        text = BROWSER_REFERENCE.read_text(encoding="utf-8")
        for name in _browser_parsers():
            assert f"### `browser {name}`" in text

    def test_uses_lf_line_endings(self):
        assert b"\r\n" not in BROWSER_REFERENCE.read_bytes()

    def test_generator_writes_it_beside_the_main_reference(self, tmp_path):
        out = tmp_path / "reference.md"
        proc = subprocess.run(
            [sys.executable, str(GENERATOR), str(out)],
            capture_output=True, text=True, cwd=REPO,
        )
        assert proc.returncode == 0, proc.stderr
        written = tmp_path / "browser-reference.md"
        assert written.read_bytes() == BROWSER_REFERENCE.read_bytes()
