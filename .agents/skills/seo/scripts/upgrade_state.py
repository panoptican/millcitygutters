#!/usr/bin/env python3
"""Bring a repo's .seo/ state directory up to the version this skill expects.

One entry point for every repo the skill lands in:

  fresh    no .seo/, no .aeo/, no docs/seo-sprint.md. Builds the v2 skeleton
           from assets/ so the foundation interview has somewhere to write.
  legacy   .aeo/ and/or docs/seo-sprint.md still exist, or config.json is the
           old flat shape. Folds them into .seo/ (this was migrate_state.py),
           merges the two brand files, and nests the config.
  partial  a .seo/ from an older version of the skill. Adds only the pieces
           that version did not have.
  current  nothing to do.

What each version added on top of the one before:

  2.0  the nested config and the .seo/ layout itself.
  2.1  the demand radar and the census: radar.md, truth-checks.json,
       needs-you.md, .seo/census/, .seo/gsc/ and the "radar" config block.
  2.2  the weekly panels and the distribute lane: .seo/competitors/,
       .seo/serp/, .seo/backlinks/, the "repo", "serp" and "distribute"
       config blocks, the weekly and monthly cadence keys, site.brand_regex
       and competitors[].sitemap_url. outcomes.json and priors.json are not
       scaffolded; scripts/outcomes.py writes both on its first run.

Everything is idempotent and conservative: it never overwrites a file that
already exists and never overwrites a key that already has a value. Anything it
declines to touch it says so about, so a half-upgraded repo is visible instead
of silent.

Usage
  upgrade_state.py                       print the plan, touch nothing
  upgrade_state.py --apply               do it
  upgrade_state.py --root path --apply   somewhere other than cwd
  upgrade_state.py --json                machine-readable plan or result

Exit codes: 0 normally, 2 on a hard error (unreadable config, bad --root).
Standard library only.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL_DIR, "assets")

CURRENT_VERSION = "2.2"

# .seo/<file>  <-  assets/<template>.  None means the file has a literal seed
# below instead of a template. brand.md is deliberately absent: the foundation
# interview owns it and writing a stub would make it look already answered.
TEMPLATE_FILES = (
    (".seo/config.json", "config.template.json"),
    (".seo/truth-checks.json", None),
    (".seo/needs-you.md", "needs-you-template.md"),
    (".seo/radar.md", "radar-template.md"),
    (".seo/content-ledger.md", "content-ledger-template.md"),
    (".seo/link-inventory.md", "link-inventory-template.md"),
    (".seo/truth.md", "truth.template.md"),
    (".seo/attributes.md", "attributes.template.md"),
)

LITERAL_SEEDS = {
    ".seo/truth-checks.json": "[]\n",
}

SKELETON_DIRS = (
    ".seo/briefs",
    ".seo/evidence",
    ".seo/health",
    ".seo/gsc",
    ".seo/census",
    ".seo/runs",
    ".seo/aeo",
    ".seo/competitors",
    ".seo/serp",
    ".seo/backlinks",
)

# Files and dirs v2.1 added on top of v2.0. Used only for the "is this repo
# already current" test; creation goes through the manifest above.
V21_ADDITIONS = (".seo/radar.md", ".seo/truth-checks.json", ".seo/needs-you.md",
                 ".seo/census", ".seo/gsc")

# Dirs v2.2 added on top of v2.1. Same role as V21_ADDITIONS. The two state
# files of that release (outcomes.json, priors.json) are deliberately absent:
# scripts/outcomes.py creates them, so their absence does not mean "not
# current".
V22_ADDITIONS = (".seo/competitors", ".seo/serp", ".seo/backlinks")

# Old top-level config keys. Their presence with no nested equivalent is what
# makes a config "flat".
FLAT_KEYS = ("domain", "gsc_site_url", "stack", "doc_path", "brand_path",
             "routes_file", "marketing_controller", "marketing_pages_dir",
             "landing_pages_dir", "site_header_path", "site_footer_path",
             "keyword_research_path", "link_inventory_path", "html_layout",
             "public_paths_constant", "routing_convention",
             "component_language", "ssr_enabled", "initialized_at")

# Present-but-unhandled leftovers from the pre-v2 skills. Reported, never moved.
LEGACY_SIGNALS = (".seo/off-page-status.md", ".seo/backlink-targets.json")

# .aeo/ migration: these two are promoted to the top of .seo/, config.json is
# merged under an "aeo" key, everything else drops into .seo/aeo/ unchanged.
PROMOTE = ("truth.md", "attributes.md")
JUNK = (".DS_Store",)

ROADMAP_STUB = "Moved to .seo/roadmap.md\n"


class HardError(Exception):
    pass


def has_flat_keys(cfg):
    """True only for genuinely pre-v2 keys.

    `stack` is in FLAT_KEYS but v2 reuses the name for the nested object, so a
    dict there is the new shape, not a leftover.
    """
    for k in FLAT_KEYS:
        if k not in cfg:
            continue
        if k == "stack" and isinstance(cfg[k], dict):
            continue
        return True
    return False


def vtuple(v):
    try:
        return tuple(int(p) for p in str(v).split("."))
    except (TypeError, ValueError):
        return (0,)


class Upgrader(object):
    """Plans and (with apply=True) performs the upgrade.

    A dry run has to model the filesystem it is not touching, or it prints
    "mkdir .seo/runs" three times and then reports files it already said it
    would create as missing. `self.created` and `self.removed` are that model;
    every filesystem question goes through the helpers below, never through os.
    """

    def __init__(self, root, apply_changes):
        self.root = os.path.abspath(root)
        self.apply = apply_changes
        self.actions = []
        self.notes = []
        self.created = set()
        self.removed = set()
        # dst -> src for moves a dry run only planned, so read() can still find
        # the bytes at their old address.
        self.moved_from = {}
        # A dry run never writes, so config edits it only planned have to live
        # somewhere or the next step re-reads the pre-edit file and plans the
        # same change twice.
        self._cfg = None
        self.state = None
        self.from_version = None
        self.quiet = False

    # ------------------------------------------------------------ reporting

    def act(self, kind, msg):
        line = "%s %s" % (kind, msg)
        self.actions.append(line)
        if not self.quiet:
            print("%s%s" % ("" if self.apply else "would ", line))

    def note(self, msg):
        self.notes.append(msg)
        if not self.quiet:
            print("note: %s" % msg)

    # ---------------------------------------------------- filesystem model

    def abs(self, rel):
        return os.path.join(self.root, rel)

    def exists(self, rel):
        if rel in self.removed:
            return False
        if rel in self.created:
            return True
        return os.path.exists(self.abs(rel))

    def isdir(self, rel):
        if rel in self.removed:
            return False
        if rel in self.created:
            return not os.path.splitext(rel)[1]
        return os.path.isdir(self.abs(rel))

    def listdir(self, rel):
        try:
            names = os.listdir(self.abs(rel))
        except OSError:
            names = []
        live = [n for n in names if os.path.join(rel, n) not in self.removed]
        live += [os.path.basename(c) for c in self.created
                 if os.path.dirname(c) == rel and os.path.basename(c) not in names]
        return sorted(set(live))

    def read(self, rel):
        path = self.abs(rel)
        if not os.path.exists(path) and rel in self.moved_from:
            return self.read(self.moved_from[rel])
        with open(path) as fh:
            return fh.read()

    def mkdir(self, rel, quiet=False):
        if self.isdir(rel):
            return False
        if not quiet:
            self.act("mkdir", rel + "/")
        self.created.add(rel)
        self.removed.discard(rel)
        if self.apply:
            os.makedirs(self.abs(rel), exist_ok=True)
        return True

    def write(self, rel, text, kind="write", detail=""):
        self.act(kind, rel + (" %s" % detail if detail else ""))
        self.created.add(rel)
        self.removed.discard(rel)
        if self.apply:
            os.makedirs(os.path.dirname(self.abs(rel)), exist_ok=True)
            with open(self.abs(rel), "w") as fh:
                fh.write(text)

    def move(self, src, dst):
        if self.exists(dst):
            self.note("%s already exists, leaving %s in place" % (dst, src))
            return False
        self.mkdir(os.path.dirname(dst), quiet=True)
        self.act("move", "%s -> %s" % (src, dst))
        self.removed.add(src)
        self.created.add(dst)
        self.moved_from[dst] = src
        if self.apply:
            shutil.move(self.abs(src), self.abs(dst))
        return True

    def remove(self, rel):
        self.act("remove", rel + ("/" if self.isdir(rel) else ""))
        self.removed.add(rel)
        self.created.discard(rel)
        if self.apply:
            if os.path.isdir(self.abs(rel)):
                os.rmdir(self.abs(rel))
            else:
                os.remove(self.abs(rel))

    # ------------------------------------------------------------- config

    def load_config(self):
        if self._cfg is not None:
            return json.loads(json.dumps(self._cfg))
        rel = ".seo/config.json"
        if not self.exists(rel):
            return None
        if not os.path.exists(self.abs(rel)):
            return None
        try:
            cfg = json.loads(self.read(rel))
        except ValueError as ex:
            raise HardError("%s is not valid JSON (%s). Fix or delete it, then "
                            "re-run." % (rel, ex))
        if not isinstance(cfg, dict):
            raise HardError(".seo/config.json is not a JSON object. Fix or "
                            "delete it, then re-run.")
        return cfg

    def save_config(self, cfg, detail):
        self.act("update", ".seo/config.json %s" % detail)
        self.created.add(".seo/config.json")
        self._cfg = json.loads(json.dumps(cfg))
        if self.apply:
            os.makedirs(self.abs(".seo"), exist_ok=True)
            with open(self.abs(".seo/config.json"), "w") as fh:
                json.dump(cfg, fh, indent=2)
                fh.write("\n")

    def template(self, name):
        path = os.path.join(ASSETS, name)
        if not os.path.exists(path):
            raise HardError("missing skill asset: assets/%s" % name)
        with open(path) as fh:
            return fh.read()

    # ------------------------------------------------------------ detection

    def detect(self):
        has_seo = self.isdir(".seo")
        has_aeo = self.isdir(".aeo")
        sprint = "docs/seo-sprint.md"
        has_sprint = self.exists(sprint)
        sprint_is_stub = False
        if has_sprint:
            try:
                sprint_is_stub = ".seo/roadmap.md" in self.read(sprint)[:200]
            except OSError:
                pass

        if not has_seo and not has_aeo and not has_sprint:
            return "fresh", None

        cfg = self.load_config()
        nested = bool(cfg) and any(isinstance(cfg.get(k), dict)
                                   for k in ("site", "paths"))
        flat = bool(cfg) and has_flat_keys(cfg)

        signals = [s for s in LEGACY_SIGNALS if self.exists(s)]
        if signals:
            self.note("legacy leftovers present, reported but not touched: %s"
                      % ", ".join(signals))

        # Hard markers are the ones a step below actually resolves. The signals
        # above are not, or a repo that keeps one forever would read "legacy"
        # on every run for the rest of its life.
        hard = []
        if has_aeo:
            hard.append(".aeo/")
        if has_sprint and not sprint_is_stub:
            hard.append(sprint)

        if cfg is None:
            ver = None
        elif isinstance(cfg.get("version"), str):
            ver = cfg["version"]
        elif nested:
            ver = "2.0"
        else:
            ver = "1.0"

        if hard or (cfg is not None and flat and not nested):
            return "legacy", "1.0"

        if ver == CURRENT_VERSION and self.scaffold_complete():
            return "current", ver
        return "partial", ver or "1.0"

    def scaffold_complete(self):
        for rel, _ in TEMPLATE_FILES:
            if not self.exists(rel):
                return False
        for rel in SKELETON_DIRS:
            if not self.isdir(rel):
                return False
        for rel in V21_ADDITIONS:
            if not self.exists(rel):
                return False
        for rel in V22_ADDITIONS:
            if not self.exists(rel):
                return False
        return True

    # ------------------------------------------------------- step: legacy

    def legacy_to_v2(self):
        self.migrate_aeo()
        self.merge_brand()
        self.migrate_roadmap()

    def migrate_aeo(self):
        if not self.isdir(".aeo"):
            return
        self.mkdir(".seo", quiet=True)

        for name in PROMOTE:
            src = ".aeo/" + name
            if self.exists(src):
                self.move(src, ".seo/" + name)

        self.merge_aeo_config()

        rest = [n for n in self.listdir(".aeo")
                if n not in PROMOTE and n != "config.json" and n not in JUNK]
        if rest:
            self.mkdir(".seo/aeo")
        for name in rest:
            self.move(".aeo/" + name, ".seo/aeo/" + name)

        for name in JUNK:
            if self.exists(".aeo/" + name):
                self.remove(".aeo/" + name)

        leftovers = self.listdir(".aeo")
        if leftovers:
            self.note(".aeo/ still holds %s, so the directory is left in place"
                      % ", ".join(leftovers))
        else:
            self.remove(".aeo")

    def merge_aeo_config(self):
        src = ".aeo/config.json"
        if not self.exists(src):
            return
        try:
            aeo_cfg = json.loads(self.read(src))
        except ValueError as ex:
            self.note("could not parse %s (%s), leaving it in place" % (src, ex))
            return
        merged = self.load_config()
        existing = merged is not None
        if merged is None:
            merged = {}
        if "aeo" in merged:
            self.note(".seo/config.json already has an \"aeo\" key, leaving it "
                      "and %s alone" % src)
            return
        merged["aeo"] = aeo_cfg
        self.save_config(merged, "(%s key \"aeo\" from %s)"
                         % ("merged" if existing else "created with", src))
        self.remove(src)

    def merge_brand(self):
        aeo_brand = ".seo/aeo/brand.md"
        seo_brand = ".seo/brand.md"
        if not self.exists(aeo_brand):
            return
        if not self.exists(seo_brand):
            self.move(aeo_brand, seo_brand)
            return

        try:
            aeo_text = self.read(aeo_brand)
            seo_text = self.read(seo_brand)
        except OSError as ex:
            self.note("could not read a brand file (%s), leaving both alone" % ex)
            return

        have = set()
        for line in seo_text.splitlines():
            if line.startswith("## "):
                have.add(line.strip().lower())

        sections, current = [], None
        for line in aeo_text.splitlines():
            if line.startswith("## "):
                current = [line]
                sections.append(current)
            elif current is not None:
                current.append(line)

        new = [s for s in sections if s[0].strip().lower() not in have]
        if not new:
            self.note("%s adds no new ## sections to %s"
                      % (aeo_brand, seo_brand))
        else:
            body = seo_text
            if not body.endswith("\n"):
                body += "\n"
            body += "\n<!-- merged from .aeo/brand.md on %s -->\n\n" % today()
            for sec in new:
                body += "\n".join(sec).rstrip() + "\n\n"
            self.write(seo_brand, body, kind="append to",
                       detail="(%d section%s from .aeo/brand.md)"
                              % (len(new), "" if len(new) == 1 else "s"))
        self.remove(aeo_brand)

    def migrate_roadmap(self):
        src = "docs/seo-sprint.md"
        dst = ".seo/roadmap.md"
        if not self.exists(src):
            return
        try:
            if ".seo/roadmap.md" in self.read(src)[:200]:
                return  # already the pointer stub
        except OSError:
            return
        if self.exists(dst):
            self.note("%s already exists, leaving %s in place" % (dst, src))
            return
        self.mkdir(".seo", quiet=True)
        self.move(src, dst)
        self.write(src, ROADMAP_STUB, detail="(pointer stub)")

    # -------------------------------------------------------- step: v2.1

    def add_radar_census(self):
        # The files and dirs v2.1 introduced are in the shared manifest, so
        # ensure_scaffold() creates them. What is specific to this step is the
        # config block that drives the demand radar.
        cfg = self.load_config()
        if cfg is None or isinstance(cfg.get("radar"), dict):
            return
        try:
            tmpl = json.loads(self.template("config.template.json"))
        except ValueError as ex:
            raise HardError("assets/config.template.json is not valid JSON (%s)"
                            % ex)
        cfg["radar"] = tmpl.get("radar", {})
        self.save_config(cfg, "(add \"radar\" block)")

    # -------------------------------------------------------- step: v2.2

    def add_v22_config(self):
        # The three dirs v2.2 introduced are in SKELETON_DIRS, so
        # ensure_scaffold() creates them, and outcomes.json / priors.json are
        # scripts/outcomes.py's to create. What is specific to this step is
        # the config behind the weekly panels and the distribute lane. Purely
        # additive: an existing key, block or comment always wins.
        cfg = self.load_config()
        if cfg is None:
            return
        try:
            tmpl = json.loads(self.template("config.template.json"))
        except ValueError as ex:
            raise HardError("assets/config.template.json is not valid JSON (%s)"
                            % ex)
        added = []

        for block in ("repo", "serp", "distribute"):
            if block not in cfg and block in tmpl:
                cfg[block] = tmpl[block]
                added.append(block)

        cadence = cfg.get("cadence")
        if isinstance(cadence, dict):
            for key, value in tmpl.get("cadence", {}).items():
                if key.startswith("_") or key in cadence:
                    continue
                cadence[key] = value
                added.append("cadence.%s" % key)
        elif "cadence" not in cfg and "cadence" in tmpl:
            cfg["cadence"] = tmpl["cadence"]
            added.append("cadence")

        site = cfg.get("site")
        if isinstance(site, dict) and "brand_regex" not in site:
            site["brand_regex"] = None
            added.append("site.brand_regex")

        competitors = cfg.get("competitors")
        if isinstance(competitors, list):
            for i, comp in enumerate(competitors):
                if isinstance(comp, dict) and "sitemap_url" not in comp:
                    comp["sitemap_url"] = None
                    added.append("competitors[%d].sitemap_url" % i)

        if added:
            self.save_config(cfg, "(add v2.2 config: %s)" % ", ".join(added))

    # ------------------------------------------------------- always-on

    def ensure_scaffold(self):
        for rel, tmpl in TEMPLATE_FILES:
            if self.exists(rel):
                continue
            text = LITERAL_SEEDS.get(rel)
            if text is None:
                text = self.template(tmpl)
            self.mkdir(os.path.dirname(rel), quiet=True)
            self.write(rel, text,
                       detail="(from assets/%s)" % tmpl if tmpl else "(empty list)")
        for rel in SKELETON_DIRS:
            self.mkdir(rel)

    def ensure_config_v2(self):
        """Derive the nested v2 shape from whatever flat keys are present.

        Purely additive. An existing nested value always wins, so running this
        on an already-nested config changes nothing.
        """
        cfg = self.load_config()
        if cfg is None:
            return
        try:
            tmpl = json.loads(self.template("config.template.json"))
        except ValueError as ex:
            raise HardError("assets/config.template.json is not valid JSON (%s)"
                            % ex)
        changed = []

        def nest(block, key, value):
            if value is None:
                return
            sub = cfg.get(block)
            if not isinstance(sub, dict):
                if block in cfg and block != "stack":
                    return
                sub = {}
                cfg[block] = sub
            if sub.get(key) in (None, ""):
                sub[key] = value
                changed.append("%s.%s" % (block, key))

        # stack was a plain string in v1; it becomes a dict whose kind holds it.
        stack_kind = None
        if isinstance(cfg.get("stack"), str):
            stack_kind = cfg["stack"]
            cfg["stack"] = {}
            changed.append("stack -> object")

        domain = cfg.get("domain")
        nest("site", "domain", domain)
        if domain:
            host = re.sub(r"^https?://", "", str(domain)).strip("/")
            nest("site", "sitemap_url", "https://%s/sitemap.xml" % host)
        nest("gsc", "site_url", cfg.get("gsc_site_url"))
        nest("stack", "kind", stack_kind)
        nest("stack", "routes_file", cfg.get("routes_file"))
        nest("stack", "marketing_controller", cfg.get("marketing_controller"))
        nest("stack", "pages_dir", cfg.get("marketing_pages_dir"))
        nest("stack", "header_component", cfg.get("site_header_path"))
        nest("stack", "footer_component", cfg.get("site_footer_path"))

        # doc_path only wins if the roadmap really is still in docs/. After the
        # move above it points at the pointer stub, which is worse than useless.
        roadmap = ".seo/roadmap.md"
        if not self.exists(roadmap) and cfg.get("doc_path"):
            roadmap = cfg["doc_path"]
        nest("paths", "roadmap", roadmap)
        for key, default in (("ledger", ".seo/content-ledger.md"),
                             ("truth", ".seo/truth.md"),
                             ("needs_you", ".seo/needs-you.md"),
                             ("runs", ".seo/runs/"),
                             ("health", ".seo/health/"),
                             ("briefs", ".seo/briefs/"),
                             ("evidence", ".seo/evidence/")):
            nest("paths", key, default)
        for block in ("budget", "select", "bing", "radar"):
            if block not in cfg and block in tmpl:
                cfg[block] = tmpl[block]
                changed.append(block)

        if has_flat_keys(cfg) and "_legacy_keys_note" not in cfg:
            cfg["_legacy_keys_note"] = (
                "Flat pre-v2 keys are kept for anything that still reads them. "
                "The nested blocks above are authoritative. `stack` was a "
                "string in v1; its value now lives at stack.kind.")
            changed.append("_legacy_keys_note")

        if changed:
            self.save_config(cfg, "(derive %s)" % ", ".join(changed))

    def set_version(self):
        cfg = self.load_config()
        if cfg is None:
            return
        if cfg.get("version") == CURRENT_VERSION:
            return
        old = cfg.get("version")
        cfg["version"] = CURRENT_VERSION
        self.save_config(cfg, "(version %s -> %s)"
                         % (old or "unset", CURRENT_VERSION))

    def seed_fresh_config(self):
        """Fresh repos get the template verbatim, pinned and not yet initialized."""
        if self.exists(".seo/config.json"):
            return
        try:
            cfg = json.loads(self.template("config.template.json"))
        except ValueError as ex:
            raise HardError("assets/config.template.json is not valid JSON (%s)"
                            % ex)
        cfg["version"] = CURRENT_VERSION
        cfg["initialized"] = False
        if isinstance(cfg.get("paths"), dict):
            cfg["paths"].setdefault("evidence", ".seo/evidence/")
        self.mkdir(".seo", quiet=True)
        self._cfg = json.loads(json.dumps(cfg))
        self.write(".seo/config.json",
                   json.dumps(cfg, indent=2) + "\n",
                   detail="(from assets/config.template.json, version %s, "
                          "initialized false)" % CURRENT_VERSION)

    # ------------------------------------------------------------ run record

    def write_run_record(self):
        rel = ".seo/runs/%s-upgrade.md" % today()
        body = ["# State upgrade %s" % today(),
                "",
                "- state detected: %s" % self.state,
                "- version: %s -> %s" % (self.from_version or "none",
                                         CURRENT_VERSION),
                "",
                "## Steps applied",
                ""]
        body += ["- %s" % a for a in self.actions] or ["- none"]
        body += ["", "## Declined to touch", ""]
        body += ["- %s" % n for n in self.notes] or ["- nothing"]
        text = "\n".join(body) + "\n"
        existing = ""
        if os.path.exists(self.abs(rel)):
            try:
                existing = self.read(rel).rstrip() + "\n\n---\n\n"
            except OSError:
                existing = ""
        if self.apply:
            os.makedirs(self.abs(".seo/runs"), exist_ok=True)
            with open(self.abs(rel), "w") as fh:
                fh.write(existing + text)
        return rel

    # ------------------------------------------------------------------ run

    def run(self):
        self.state, self.from_version = self.detect()

        if self.state == "fresh":
            print_plan_header(self.quiet,
                              "fresh: foundation will build .seo/ from templates")
            self.seed_fresh_config()
            self.ensure_scaffold()
        elif self.state == "current":
            print_plan_header(self.quiet, "current: nothing to do")
        else:
            print_plan_header(
                self.quiet,
                "%s: upgrading state from %s to %s"
                % (self.state, self.from_version, CURRENT_VERSION))
            steps = [(v, f) for v, f in UPGRADES
                     if vtuple(v) > vtuple(self.from_version)]
            for version, step in steps:
                step(self)
            self.ensure_scaffold()
            self.ensure_config_v2()

        self.set_version()

        record = None
        if self.apply and self.actions:
            record = self.write_run_record()
            if not self.quiet:
                print("wrote %s" % record)
        return record


# Ordered v-target -> step. Every step whose target is newer than the version
# found in config.json runs, oldest first.
UPGRADES = [
    ("2.0", Upgrader.legacy_to_v2),
    ("2.1", Upgrader.add_radar_census),
    ("2.2", Upgrader.add_v22_config),
]


def today():
    return datetime.date.today().isoformat()


def print_plan_header(quiet, msg):
    if not quiet:
        print(msg)
        print("")


def main():
    ap = argparse.ArgumentParser(
        description="Bring a repo's .seo/ state directory up to version %s. "
                    "Idempotent; never overwrites. Prints the plan and changes "
                    "nothing unless --apply is given." % CURRENT_VERSION)
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--apply", action="store_true",
                    help="perform the plan (default is a dry run)")
    ap.add_argument("--json", action="store_true",
                    help="print the plan or result as JSON and nothing else")
    ap.add_argument("--dry-run", action="store_true",
                    help="no-op; a dry run is already the default")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print("no such directory: %s" % args.root, file=sys.stderr)
        return 2

    up = Upgrader(args.root, args.apply and not args.dry_run)
    up.quiet = args.json
    try:
        up.run()
    except HardError as ex:
        if args.json:
            print(json.dumps({"error": str(ex)}, indent=2))
        print("error: %s" % ex, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "state": up.state,
            "from_version": up.from_version,
            "to_version": CURRENT_VERSION,
            "actions": up.actions,
            "notes": up.notes,
        }, indent=2))
    else:
        print("")
        print("SUMMARY: state=%s %d action%s (%s)"
              % (up.state, len(up.actions),
                 "" if len(up.actions) == 1 else "s",
                 "applied" if up.apply else "dry run"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
