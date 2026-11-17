"""The acquisition guide stays true and reachable.

`acquisition.md` and the generated `browser-reference.md` sit beside SKILL.md
and are read only when SKILL.md sends an agent there, so they are kept out of
the context-cost measurement. That makes them easy to forget: a guide showing
a flag the CLI dropped, or a pointer that resolves on one install target and
not another, fails silently. These tests apply the checks that
`test_skill_reference_current.py` and `test_skill_install.py` apply to
SKILL.md and reference.md; `test_browser_reference.py` keeps the generated
browser reference current.
"""

import argparse
import re
from pathlib import Path

import pytest

from zotero_mcp.skill_install import (
    ON_DEMAND_FILES,
    SKILL_NAME,
    install_skill,
    packaged_skill_dir,
)

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "src" / "zotero_mcp" / "skills" / "zotero-cli"
SKILL_MD = SKILL_DIR / "SKILL.md"
GUIDE = SKILL_DIR / "acquisition.md"


@pytest.fixture(autouse=True)
def fake_home(tmp_path_factory, monkeypatch):
    """Keep the claude-user target out of the real home directory."""
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    return home


def _browser_parsers() -> dict[str, argparse.ArgumentParser]:
    from zotero_mcp.cli_standalone import build_parser

    def subcommands(parser):
        action = next(a for a in parser._actions
                      if isinstance(a, argparse._SubParsersAction))
        return action.choices

    return dict(subcommands(subcommands(build_parser())["browser"]))


class TestGuideAccuracy:
    """Every command and flag the guide shows must actually exist."""

    @staticmethod
    def _cli_tokens():
        from zotero_mcp.cli_standalone import build_parser

        commands: set[str] = set()
        flags: set[str] = {"--json", "--json-schema", "-v", "--verbose"}

        def walk(p):
            for action in p._actions:
                flags.update(action.option_strings)
                if isinstance(action, argparse._SubParsersAction):
                    for name, sub in action.choices.items():
                        commands.add(name)
                        walk(sub)

        walk(build_parser())
        return commands, flags

    @staticmethod
    def _command_lines():
        body = GUIDE.read_text(encoding="utf-8")
        for block in re.findall(r"```bash\n(.*?)```", body, re.DOTALL):
            yield from (line for line in block.splitlines() if "zotero-cli" in line)

    def test_every_flag_shown_exists(self):
        _, flags = self._cli_tokens()
        body = GUIDE.read_text(encoding="utf-8")
        shown = set(re.findall(r"`--[a-z][a-z-]*", body))
        for line in self._command_lines():
            shown.update(re.findall(r"(?<![\w-])(--[a-z][a-z-]*)", line))
        shown = {s.lstrip("`") for s in shown}
        unknown = sorted(shown - flags)
        assert not unknown, f"acquisition.md shows flags the CLI does not accept: {unknown}"

    def test_every_command_shown_exists(self):
        commands, _ = self._cli_tokens()
        shown = set()
        for line in self._command_lines():
            match = re.search(r"zotero-cli\s+((?:--\S+\s+)*)([a-z-]+)", line)
            if match:
                shown.add(match.group(2))
        unknown = sorted(shown - commands - {"config"})
        assert not unknown, f"acquisition.md shows commands that do not exist: {unknown}"

    def test_browser_examples_use_their_own_subcommands_flags(self):
        """A flag that exists on `browser batch` but not on `browser save`
        still fails when shown on a save line."""
        parsers = _browser_parsers()
        checked = 0
        for line in self._command_lines():
            match = re.search(r"zotero-cli\s+(?:--\S+\s+)*browser\s+([a-z-]+)", line)
            if not match:
                continue
            sub = parsers[match.group(1)]
            accepted = {s for a in sub._actions for s in a.option_strings}
            shown = set(re.findall(r"(?<![\w-])(--[a-z][a-z-]*)", line[match.end():]))
            assert shown <= accepted, (
                f"`browser {match.group(1)}` does not accept {sorted(shown - accepted)}"
            )
            checked += 1
        assert checked, "acquisition.md shows no browser commands"


class TestPointers:
    def test_skill_md_points_only_at_files_that_ship(self):
        named = re.findall(r"`([\w.-]+)` in this skill directory",
                           SKILL_MD.read_text(encoding="utf-8"))
        assert "acquisition.md" in named
        for name in named:
            assert name in ON_DEMAND_FILES
            assert (packaged_skill_dir() / name).is_file()

    def test_every_on_demand_file_ships(self):
        for name in ON_DEMAND_FILES:
            assert (packaged_skill_dir() / name).is_file()

    def test_guide_links_resolve_inside_the_skill_directory(self):
        """Every install target copies the skill directory whole, so a link
        that stays inside it resolves everywhere; one that leaves it does not."""
        links = re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", GUIDE.read_text(encoding="utf-8"))
        assert "browser-reference.md" in links
        for link in links:
            assert "/" not in link, f"{link} leaves the skill directory"
            assert (SKILL_DIR / link).is_file()


class TestInstalledCopies:
    @pytest.mark.parametrize("target,skill_dir", [
        ("claude", ".claude/skills"),
        ("cursor", ".agents/skills"),
        ("windsurf", ".agents/skills"),
        ("agents", ".agents/skills"),
    ])
    def test_on_demand_files_land_in_the_skill_copy(self, tmp_path, target, skill_dir):
        if target == "claude":
            (tmp_path / ".claude").mkdir()
        results = install_skill([target], root=tmp_path)
        assert results[0].status == "installed"
        for name in ON_DEMAND_FILES:
            assert (tmp_path / skill_dir / SKILL_NAME / name).is_file()

    @pytest.mark.parametrize("target", ["claude", "cursor", "windsurf"])
    def test_results_list_the_on_demand_files(self, tmp_path, target):
        if target == "claude":
            (tmp_path / ".claude").mkdir()
        paths = install_skill([target], root=tmp_path)[0].paths
        for name in ON_DEMAND_FILES:
            assert any(p.name == name for p in paths), f"{name} missing from {paths}"
        for path in paths:
            assert path.is_file()

    @pytest.mark.parametrize("target,rule", [
        ("cursor", ".cursor/rules/zotero-cli.mdc"),
        ("windsurf", ".windsurf/rules/zotero-cli.md"),
    ])
    def test_rule_body_points_at_the_guide_where_it_was_installed(
        self, tmp_path, target, rule
    ):
        install_skill([target], root=tmp_path)
        text = (tmp_path / rule).read_text(encoding="utf-8")
        assert "in this skill directory" not in text
        assert "`.agents/skills/zotero-cli/acquisition.md`" in text
        assert (tmp_path / ".agents" / "skills" / SKILL_NAME / "acquisition.md").is_file()
        rules_dir = (tmp_path / rule).parent
        assert [p.name for p in rules_dir.iterdir()] == [Path(rule).name]
