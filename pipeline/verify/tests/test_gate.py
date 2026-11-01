"""The gate's tests. They use no models and no money.

    python -m unittest discover -s pipeline/verify/tests -t . -v
"""
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from .. import answers, backend, blind, difficulty, gate, originality, prompts, run_seeds, sandbox, standard
from ..config import ROOT, corpus_path
from .scripted import ScriptedBackend

HERE = Path(__file__).resolve().parent
EXPECTED = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
DRAFTS = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (HERE / "drafts").glob("*.json")}
# A fixed ruler, so these tests don't move whenever thresholds.json is refitted.
TH = {"provisional": True, "too_easy_tokens": 400, "cuts": [{"kyu": 8, "max_score": 3.5}, {"kyu": 7, "max_score": 3.8}, {"kyu": 6, "max_score": 4.0}, {"kyu": 5, "max_score": 4.3}, {"kyu": 4, "max_score": 4.6}, {"kyu": 3, "max_score": 6.5}]}
BANK_INDEX = originality.Index(originality.load_bank())


def ruler_for(d):
    """Accepts any score at the draft's own kyu. Difficulty has its own tests, and mis-rated-hard uses the real ruler."""
    return {**TH, "cuts": [{"kyu": d["kyu"], "max_score": 99}]}


def run(pid, **kw):
    be = ScriptedBackend(DRAFTS, {k: v["sim"] for k, v in EXPECTED.items()})
    # Figures have their own tests in pipeline/figures, and these drafts are about everything else.
    with mock.patch.object(gate.figure_check, "run", return_value=("pass", "stubbed", dict(figures=[], renders=[]))):
        return _verify(pid, be, **kw)


def _verify(pid, be, **kw):
    return gate.verify(DRAFTS[pid], be, sandbox_seconds=8, thresholds=TH if pid == "mis-rated-hard" else ruler_for(DRAFTS[pid]), index=BANK_INDEX, has_corpus=False, auto_fail=0.6, **kw), be


def name_in(verdict):
    m = re.match(r"\w+ (\w+):", verdict)
    return m.group(1) if m else None


class Suite(unittest.TestCase):
    def test_every_draft_gets_its_expected_verdict(self):
        self.assertGreaterEqual(len(DRAFTS), 40)
        for pid in sorted(DRAFTS):
            with self.subTest(pid):
                report, _ = run(pid)
                e = EXPECTED[pid]
                self.assertIn(report["verdict"].split(" ")[0], e["verdict"], report["verdict"])
                if e["checks"]:
                    allowed = {c.replace("originality_lexical", "originality") for c in e["checks"]}
                    self.assertIn(name_in(report["verdict"]), allowed, report["verdict"])

    def test_cheap_failures_never_reach_a_model(self):
        for pid in ("bad-key-digit-product", "hard-coded-literal", "sandbox-network", "schema-bad-kyu", "standard-one-hint", "latex-undefined-macro", "near-copy-of-bank-digit-weight"):
            with self.subTest(pid):
                report, be = run(pid)
                self.assertEqual(be.prompts, [], report["verdict"])

    def test_blind_solvers_get_only_the_statement(self):
        _, be = run("ok-digit-product")
        d = DRAFTS["ok-digit-product"]
        solves = [p for role, _, p in be.prompts if role == "solve"]
        self.assertEqual(len(solves), 7)
        for p in solves:
            self.assertEqual(p, d["statement"])

    def test_investigate_when_majority_disagrees_and_critics_clean(self):
        d = DRAFTS["ok-seven-divides"]
        be = ScriptedBackend({d["id"]: d}, {d["id"]: {"solves": ["30"] * 7}})
        report = gate.verify(d, be, sandbox_seconds=8, thresholds=ruler_for(d), index=BANK_INDEX, has_corpus=False, auto_fail=0.6)
        self.assertTrue(report["verdict"].startswith("INVESTIGATE blind_solves"), report["verdict"])

    def test_keep_going_lists_every_failure_and_names_the_first_in_brief_order(self):
        report, _ = run("standard-one-hint", keep_going=True)
        self.assertEqual(report["verdict"].split(":")[0], "FAIL standard")
        self.assertGreater(report["usage"]["calls"], 5)

    def test_proof_path_skips_computation(self):
        report, be = run("proof-ok")
        self.assertEqual(report["verdict"], "PASS")
        self.assertFalse([p for role, _, p in be.prompts if role == "solve"])
        self.assertIn("skip", [c["status"] for c in report["checks"] if c["check"] == "computational"])


class Blind(unittest.TestCase):
    d = {"answer": "25/4", "kyu": 5}

    def solves(self, values, tokens=900):
        rows = [dict(model="claude-sonnet-5-5", canon=answers.canon(v) if v else None, output_tokens=tokens) for v in values]
        return rows

    def test_four_of_seven_passes(self):
        self.assertEqual(blind.analyse(self.d, self.solves(["6.25"] * 4 + ["1"] * 3), 400)[0], "pass")

    def test_fractions_and_decimals_agree(self):
        self.assertEqual(blind.analyse(self.d, self.solves(["25/4", "6.25", "6.250", "1", "2", "3", ""]), 400)[2]["right"], 3)

    def test_majority_elsewhere_is_investigate(self):
        status, reason, _ = blind.analyse(self.d, self.solves(["9"] * 5 + ["6.25"] * 2), 400)
        self.assertEqual(status, "investigate")
        self.assertIn("wrong key", reason)

    def test_no_majority_is_investigate(self):
        self.assertEqual(blind.analyse(self.d, self.solves(["1", "2", "3", "4", "5", "6.25", "6.25"]), 400)[0], "investigate")

    def test_too_easy_only_at_5_kyu_or_harder(self):
        self.assertEqual(blind.analyse(self.d, self.solves(["6.25"] * 7, 100), 400)[0], "fail")
        self.assertEqual(blind.analyse({**self.d, "kyu": 6}, self.solves(["6.25"] * 7, 100), 400)[0], "pass")
        self.assertEqual(blind.analyse(self.d, self.solves(["6.25"] * 7, 2000), 400)[0], "pass")

    def test_too_easy_only_investigates_on_a_provisional_ruler(self):
        self.assertEqual(blind.analyse(self.d, self.solves(["6.25"] * 7, 100), 400, provisional=True)[0], "investigate")


class Answers(unittest.TestCase):
    def test_tidy(self):
        for raw, want in [("$\\dfrac{25}{4}$", "25/4"), ("130^\\circ", "130"), ("20 km/h", "20"), ("\\boxed{29}", "29"), ("1,024", "1,024"), ("29.", "29")]:
            self.assertEqual(answers.tidy(raw), want)
        self.assertEqual(answers.canon(answers.tidy("1,024")), "1024")

    def test_hash_matches_the_sites(self):
        self.assertEqual(answers.answer_hash("circle-in-the-square", "25/4"), "a7169a50")


class Sandbox(unittest.TestCase):
    def test_runtime_blocks_what_the_static_check_would_miss(self):
        for src in ("import sys\nsys.modules['importlib'].import_module('socket').socket()",
                    "import sys\nsys.modules['os'].system('echo hi')",
                    "import sys\nsys.modules['io'].FileIO('x.txt', 'w')",
                    "import sys\nsys.modules['io'].FileIO(sys.modules['os'].path.expanduser('~/.gitconfig'))"):
            r = sandbox.run_program(src, seconds=20)
            self.assertFalse(r.ok, src)
            self.assertIn("sandbox", r.error, src)

    def test_import_guard_applies_at_runtime(self):
        self.assertIn("not allowed", sandbox.run_program("import socket", seconds=20).error)

    def test_sympy_and_numpy_work(self):
        r = sandbox.run_program("import numpy as np\nfrom sympy import isprime, Rational\nprint(int(np.arange(4).sum()) + int(isprime(7)) + Rational(1, 2) * 2)", seconds=20)
        self.assertEqual(r.stdout.strip(), "8", r.error)

    def test_static_check(self):
        self.assertTrue(sandbox.static_check("print(505)")[1])
        self.assertTrue(sandbox.static_check("a = 5\nprint(a * a)")[1])
        self.assertFalse(sandbox.static_check("print(sum(range(5)))")[1])
        self.assertIn("not allowed", sandbox.static_check("import subprocess")[0])
        self.assertIn("not allowed", sandbox.static_check("print(().__class__)")[0])
        self.assertIn("not allowed", sandbox.static_check("open('x')")[0])
        self.assertIn("not allowed", sandbox.static_check("import random")[0])


TAXONOMY = {"casework": "observed", "rule-of-product": "observed", "polynomial-factoring": "observed", "vieta": "seeded","pigeonhole": "seeded", "perpendicular-from-center-to-chord": "observed"}


class Critics(unittest.TestCase):
    def test_audit_prompt_gives_the_hints_and_a_bad_hint_fails(self):
        d = DRAFTS["ok-seat-row"]
        audit = {"reaches_answer": True, "issues": [{"severity": "material", "issue": "Hint 1: it only restates the statement"}]}
        be = ScriptedBackend({d["id"]: d}, {d["id"]: {"audit": audit}})
        report = gate.verify(d, be, sandbox_seconds=8, thresholds=ruler_for(d), index=BANK_INDEX, has_corpus=False, auto_fail=0.6)
        self.assertEqual(report["verdict"], "FAIL solution_audit: Hint 1: it only restates the statement")
        prompt = [p for role, _, p in be.prompts if role == "solution_audit"][0]
        for h in d["hints"]:
            self.assertIn(h, prompt)
        self.assertEqual(len(be.prompts), 10, "no extra model call for the hints")

    def test_well_posedness_prompt_names_what_the_standard_asks(self):
        for words in ("more than one question", "hidden case", "reading trick", "culturally specific"):
            self.assertIn(words, prompts.WELL_POSED)


class Standard(unittest.TestCase):
    def test_uk_spelling_ignores_maths_and_catches_prose(self):
        d = DRAFTS["ok-digit-product"]
        self.assertEqual(standard.run(d)[0], "pass")
        self.assertEqual(standard.run({**d, "statement": "Find the center of $x$."})[0], "fail")

    def fails(self, **changes):
        return standard.run({**DRAFTS["ok-seat-row"], **changes}, taxonomy=TAXONOMY)[2]["failures"]

    def test_taxonomy_ids_are_exempt_from_spelling(self):
        d = DRAFTS["ok-seat-row"]
        self.assertEqual(self.fails(subtopics=["perpendicular-from-center-to-chord"]), [])
        bare = d["solution"] + " See perpendicular-from-center-to-chord."
        self.assertFalse([f for f in self.fails(statement=d["statement"], hints=[*d["hints"][:1], bare]) if "S8" in f])

    def test_incenter_fails_except_in_the_books_title(self):
        s = "Let $I$ be the incenter of triangle $ABC$. Find the count."
        self.assertTrue([f for f in self.fails(statement=s) if "incentre" in f])
        self.assertTrue([f for f in self.fails(title="The Circumcenter") if "circumcentre" in f])
        s = "This is from Beyond the Incenter. Find the count."
        self.assertFalse([f for f in self.fails(statement=s) if "S8" in f])

    def test_title_and_id_cannot_give_away_technique_or_answer(self):
        self.assertTrue([f for f in self.fails(title="Vieta on a cubic") if "S13" in f])
        self.assertTrue([f for f in self.fails(title="A casework walk") if "S13" in f])
        self.assertTrue([f for f in self.fails(title="Inclusion-exclusion in a row") if "S13" in f])
        self.assertTrue([f for f in self.fails(id="pigeonhole-seats") if "S13" in f])
        self.assertTrue([f for f in self.fails(title="Exactly 8 seats") if "S13" in f])
        self.assertFalse([f for f in self.fails(title="Between friends") if "S13" in f])
        self.assertTrue([f for f in self.fails(title="An AIME warm-up") if "S12" in f])

    def test_hint_count_and_kyu_type_rules(self):
        proof = DRAFTS["proof-ok"]
        one_hint_at_5 = {**proof, "kyu": 5, "hints": proof["hints"][:1]}
        got = standard.run(one_hint_at_5, taxonomy=TAXONOMY)[2]["failures"]
        self.assertTrue([f for f in got if f.startswith("H1")], got)
        self.assertTrue([f for f in got if f.startswith("K4")], got)
        self.assertEqual(standard.run(proof, taxonomy=TAXONOMY)[0], "pass")
        self.assertTrue([f for f in self.fails(kyu=2) if f.startswith("K4")])

    def test_appendix_answer_rules(self):
        self.assertTrue([f for f in self.fails(answer_format="expression") if f.startswith("A2")])
        self.assertTrue([f for f in self.fails(answer="4/8", answer_format="rational") if f.startswith("A3")])
        self.assertTrue([f for f in self.fails(answer="1234/5", answer_format="rational") if f.startswith("A3")])
        self.assertTrue([f for f in self.fails(answer="2.5", answer_format="rational") if f.startswith("A3")])
        self.assertTrue([f for f in self.fails(answer="5/2", answer_format="rational") if f.startswith("S3")])
        self.assertTrue([f for f in self.fails(answer="1") if f.startswith("A6")])
        self.assertTrue([f for f in self.fails(answer="20") if f.startswith("A6")])
        self.assertTrue([f for f in self.fails(answer="2000000000", answer_format="integer") if f.startswith("A1")])

    def test_appendix_format_rules(self):
        self.assertTrue([f for f in self.fails(statement="Find $2*3$.") if f.startswith("S9")])
        self.assertTrue([f for f in self.fails(statement="Find $\\frac12$.") if f.startswith("S9")])
        self.assertTrue([f for f in self.fails(statement="Find $$\\frac{1}{2}$$") if f.startswith("S9")])
        self.assertTrue([f for f in self.fails(statement="Is $x \\leq 2$ true?") if f.startswith("S9")])
        self.assertTrue([f for f in self.fails(statement="Find **this** number.") if f.startswith("S10")])
        self.assertTrue([f for f in self.fails(statement="How many? And why?") if f.startswith("S1")])
        self.assertTrue([f for f in self.fails(solution="The crux is parity, so the answer is $5$.") if f.startswith("M8")])
        self.assertTrue([f for f in self.fails(solution="So $5$.\n\n<b>Why this works.</b> Parity.") if f.startswith("M8")])
        self.assertTrue([f for f in self.fails(subtopics=["not-a-slug"]) if f.startswith("M5")])
        self.assertTrue([f for f in self.fails(provenance={"kind": "original", "author": "x", "pipeline_run": "r1"}) if f.startswith("O4")])

    def test_inspired_by_stays_private(self):
        d = {**DRAFTS["ok-digit-product"], "inspired_by": "AIME-2019-I-07"}
        self.assertEqual(standard.run(d)[0], "pass")
        self.assertEqual(standard.run({**d, "solution": d["solution"] + " Compare AIME-2019-I-07."})[0], "fail")


# Invented for this test. The sentinel words make any leak easy to spot.
SENTINEL = "zebra quilt marmalade heptagon wanders past seventeen velvet lanterns before dawn each morning"


class Corpus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "corpus"
        self.dir.mkdir()
        rows = [dict(id="FAKE-01", statement_md=f"Problem: {SENTINEL}. Find the count.", answer_value=7),
                dict(id="FAKE-02", statement_md="How many primes lie between ten and thirty?", answer_value=6)]
        (self.dir / "fake.jsonl").write_text("\n".join(map(json.dumps, rows)), encoding="utf-8")
        (self.dir / "fake_analysis.jsonl").write_text(json.dumps(dict(id="FAKE-01", core_idea="Pair objects by an involution.")), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_loads_records_and_joins_core_ideas(self):
        rows = originality.load_corpus(self.dir)
        self.assertEqual([r["id"] for r in rows], ["FAKE-01", "FAKE-02"])
        self.assertEqual(rows[0]["core_idea"], "Pair objects by an involution.")
        self.assertIsNone(rows[1]["core_idea"])

    def test_env_vars_kyuclid_first(self):
        with mock.patch.dict(os.environ, {"KYUCLID_CORPUS": str(self.dir.parent), "MATHWARS_CORPUS": "elsewhere"}):
            self.assertEqual(corpus_path(), self.dir)
        with mock.patch.dict(os.environ, {"MATHWARS_CORPUS": str(self.dir)}, clear=False):
            os.environ.pop("KYUCLID_CORPUS", None)
            self.assertEqual(corpus_path(), self.dir)

    def test_core_idea_matches_when_the_words_do_not(self):
        ix = originality.Index(originality.load_corpus(self.dir))
        top = ix.similarities("Count the wombats in a tree.", core_idea="Pair objects by an involution.")[0]
        self.assertEqual(top[0]["id"], "FAKE-01")

    def test_no_corpus_text_reaches_a_report_even_if_the_judge_quotes_it(self):
        ix = originality.Index(originality.load_corpus(self.dir))
        d = {**DRAFTS["ok-digit-product"], "inspired_by": "FAKE-01"}
        quote = {"neighbours": [{"id": "FAKE-01", "reskin": True, "reason": SENTINEL}], "known": {"is_known": True, "name": SENTINEL, "reason": SENTINEL}}
        be = ScriptedBackend({d["id"]: d}, {d["id"]: {"originality": quote}})
        report = gate.verify(d, be, sandbox_seconds=8, thresholds=ruler_for(d), index=ix, has_corpus=True, auto_fail=0.99)
        text = json.dumps(report)
        self.assertIn("FAKE-01", text)
        self.assertNotIn("zebra", text)
        self.assertNotIn("marmalade", text)
        self.assertTrue(report["verdict"].startswith("FAIL originality"), report["verdict"])
        # The judge did see it: that's the point of the check.
        self.assertTrue(any("zebra" in p for role, _, p in be.prompts if role == "originality"))

    def test_corpus_prompts_are_not_cached(self):
        ix = originality.Index(originality.load_corpus(self.dir))
        d = {**DRAFTS["ok-digit-product"], "inspired_by": "FAKE-01"}
        be = ScriptedBackend({d["id"]: d})
        with mock.patch.object(be, "call", wraps=be.call) as call:
            originality.judge(d, ix, be, backend.Usage(), True)
        self.assertFalse(call.call_args.kwargs["cacheable"])

    def test_inspiration_is_always_examined(self):
        ix = originality.Index(originality.load_corpus(self.dir))
        d = {"id": "d", "statement": "How many primes lie between twenty and fifty?", "inspired_by": "FAKE-01"}
        self.assertIn("FAKE-01", [r["id"] for r in originality.neighbours_for(d, ix)])

    def test_masking_ignores_numbers_and_variable_names(self):
        ix = originality.Index(originality.load_bank())
        a = ix.similarities("How many positive integers less than $10^{18}$ have decimal digits that sum to $5$ and are divisible by $41$?")[0]
        self.assertEqual(a[0]["id"], "three-units-of-digit-weight")
        self.assertGreater(a[1], 0.9)


class Backends(unittest.TestCase):
    def test_cli_is_blind_and_cannot_bill_an_api_key(self):
        seen = {}

        def fake_run(args, **kw):
            seen.update(args=args, **kw)
            out = dict(result='{"answer":"5"}', usage={"input_tokens": 1, "output_tokens": 2, "output_tokens_details": {"thinking_tokens": 1}}, total_cost_usd=0.01, is_error=False)
            return mock.Mock(stdout=json.dumps(out), stderr="", returncode=0)

        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "stray"}), mock.patch("shutil.which", return_value="claude"), mock.patch("subprocess.run", fake_run):
            r = backend.CliBackend()._send("m", "sys", "prompt", "medium", 1000, "solve", "d", "")
        self.assertEqual((r.text, r.output, r.thinking), ('{"answer":"5"}', 2, 1))
        self.assertNotIn("ANTHROPIC_API_KEY", seen["env"])
        self.assertEqual(seen["env"]["CLAUDE_CODE_MAX_OUTPUT_TOKENS"], "1000")
        self.assertEqual(seen["input"], "prompt")
        self.assertNotEqual(Path(seen["cwd"]).resolve(), ROOT)
        for flag in ("--no-session-persistence", "--strict-mcp-config", "--setting-sources", "--tools", "--system-prompt"):
            self.assertIn(flag, seen["args"])

    def test_cli_rate_limit_stops_the_run(self):
        out = dict(result="You've hit your limit", is_error=True, api_error_status=429)
        with mock.patch("shutil.which", return_value="claude"), mock.patch("subprocess.run", return_value=mock.Mock(stdout=json.dumps(out), stderr="", returncode=1)):
            with self.assertRaises(backend.PlanLimit):
                backend.CliBackend()._send("m", "s", "p", "low", 10, "", "", "")

    def test_cli_output_cap_is_no_answer_not_an_error(self):
        out = dict(result="API Error: Claude's response exceeded the 300 output token maximum.", is_error=True, usage={"output_tokens": 1200})
        with mock.patch("shutil.which", return_value="claude"), mock.patch("subprocess.run", return_value=mock.Mock(stdout=json.dumps(out), stderr="", returncode=1)) as run:
            r = backend.CliBackend()._send("m", "s", "p", "low", 300, "", "", "")
        self.assertTrue(r.truncated)
        self.assertEqual((r.output, run.call_count), (1200, 1))
        self.assertEqual(blind._extract(r.text), "")

    def test_cli_budget_stops_retries_and_counts_as_no_answer(self):
        out = dict(subtype="error_max_budget_usd", is_error=True, stop_reason="max_tokens", usage={"output_tokens": 0}, total_cost_usd=0.17)
        with mock.patch("shutil.which", return_value="claude"), mock.patch("subprocess.run", return_value=mock.Mock(stdout=json.dumps(out), stderr="", returncode=1)) as run:
            r = backend.CliBackend()._send("claude-sonnet-5-5", "s", "p", "low", 16000, "", "", "")
        self.assertTrue(r.truncated)
        self.assertEqual((r.output, r.usd), (16000, 0.17))
        args = run.call_args.args[0]
        self.assertEqual(args[args.index("--max-budget-usd") + 1], "0.1600")

    def test_seed_table_keeps_only_ids_and_names(self):
        self.assertEqual(run_seeds.public("FAIL originality: reskin of AMC8-1991-09: Same moduli and steps."), "FAIL originality: reskin of AMC8-1991-09")
        self.assertEqual(run_seeds.public("FAIL originality: known problem: Lockers: details here."), "FAIL originality: known problem: Lockers")

    def test_api_refuses_without_a_key(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with self.assertRaises(backend.ModelError):
                backend.make_backend("api")

    def test_cached_calls_cost_nothing_now(self):
        u = backend.Usage()
        u.add(backend.Reply(text="", model="m", usd=1.0))
        u.add(backend.Reply(text="", model="m", usd=2.0, cached=True))
        s = u.summary()
        self.assertEqual((s["api_equivalent_usd"], s["api_equivalent_usd_this_run"], s["calls"]), (3.0, 1.0, 2))

    def test_last_json(self):
        self.assertEqual(backend.last_json('a {"x":1} b {"y":{"z":2}} c'), {"y": {"z": 2}})
        self.assertIsNone(backend.last_json("no json"))


class Difficulty(unittest.TestCase):
    def test_estimate_and_investigate_while_provisional(self):
        ev = dict(right=7, total=7, median_sonnet_tokens=100)
        self.assertEqual(difficulty.run({"kyu": 8}, ev, TH)[0], "pass")
        self.assertEqual(difficulty.run({"kyu": 3}, ev, TH)[0], "investigate")
        self.assertEqual(difficulty.run({"kyu": 3}, ev, {**TH, "provisional": False})[0], "fail")


class PublicRepoStaysClean(unittest.TestCase):
    """Rule 1. Scans everything this task added for 10-word runs from the corpus. Skipped without a corpus."""

    def test_no_corpus_text_in_pipeline(self):
        path = corpus_path()
        if not path or not path.is_dir():
            self.skipTest("no corpus configured")
        grams = set()
        for r in originality.load_corpus(path):
            w = re.findall(r"\w+", r["text"].lower())
            grams.update(tuple(w[i:i + 10]) for i in range(len(w) - 9))
        for f in (ROOT / "pipeline").rglob("*"):
            if f.suffix in (".py", ".json", ".md", ".mjs", ".txt"):
                w = re.findall(r"\w+", f.read_text(encoding="utf-8").lower())
                hits = [" ".join(w[i:i + 10]) for i in range(len(w) - 9) if tuple(w[i:i + 10]) in grams]
                self.assertEqual(hits, [], str(f))


if __name__ == "__main__":
    unittest.main()
