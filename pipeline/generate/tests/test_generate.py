"""No models and no corpus: a scripted backend, an invented source problem, and temp folders."""
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline.generate import config, drafts, inputs, plan, prompts, recipes, report, run
from pipeline.verify import originality
from pipeline.verify.backend import Backend, Reply

RECORD = dict(id="SRC-1", topic="N", kyu=4, techniques=["crt", "bounding"], core_idea="x", crux="y", traps=["t"], generation_potential="high", figure_needed=False,
              solution_paths=[dict(name="a", difficulty_of_path="easy", key_steps=["s"]), dict(name="b", difficulty_of_path="hard", key_steps=["s"])])
INPUT = inputs.Input("SRC-1", RECORD, "A pond holds exactly seventeen silver fish and twenty three golden fish swimming around in circles today. How many?", "40")
WHY = "<b>Why this works.</b> <code>crt</code>: residues split."
PROGRAM = "print(sum(1 for n in range(1, 100) if n % 3 == 1 and n % 5 == 2))"
STATEMENT = "How many integers $n$ with $1 \\le n \\le 99$ leave remainder $1$ on division by $3$ and remainder $2$ on division by $5$?"


def idea(title="Quiet residues", statement=STATEMENT, recipe="transplant", interest=8, program=PROGRAM):
    return (f"<candidate><title>{title}</title><recipe>{recipe}</recipe><topic>N</topic><statement>{statement}</statement><sketch>Residues.</sketch>"
            f"<check_program>{program}</check_program><interest>{interest}</interest><interest_reason>r</interest_reason></candidate>")


def write(answer="7"):
    return (f"<subtopics>crt</subtopics><hint>Look at residues.</hint><hint>Use the Chinese remainder theorem.</hint>"
            f"<solution>The residue is $7$ modulo $15$. The answer is ${answer}$.\n\n{WHY}</solution>")


class Scripted(Backend):
    def __init__(self, replies):
        super().__init__(concurrency=2, name="scripted", use_cache=False)
        self.replies, self.calls = list(replies), []

    def call(self, model, system, prompt, effort, max_tokens, salt="", cacheable=True, role="", draft_id=""):
        self.calls.append(dict(prompt=prompt, cacheable=cacheable, role=role))
        return Reply(text=self.replies.pop(0), model=model, output=100, usd=0.25)


def gate_report(*checks):
    rows = [dict(check=c, status=s, reason=r, evidence=e) for c, s, r, e in checks]
    from pipeline.verify.gate import verdict_line
    return dict(id="x", checks=rows, verdict=verdict_line(rows), plan_limit=False, usage=dict(api_equivalent_usd_this_run=0.25), notes=[])


class Parsing(unittest.TestCase):
    def test_ideas_keep_latex_and_drop_a_truncated_block(self):
        got = prompts.parse_ideas(idea() + "\n<candidate><title>Cut off</title><statement>never fin")
        self.assertEqual(len(got), 1)
        self.assertIn("\\le", got[0]["statement"])
        self.assertEqual(got[0]["interest"], 8.0)

    def test_write_up(self):
        w = prompts.parse_write_up(write())
        self.assertEqual((w["subtopics"], len(w["hints"])), (["crt"], 2))
        self.assertEqual(prompts.parse_write_up("<disagree>the key is wrong</disagree>"), dict(disagree="the key is wrong"))
        self.assertIsNone(prompts.parse_write_up("<hint>only this</hint>"))

    def test_standard_rules_use_the_ladder_row(self):
        text = prompts.idea_rules(4)
        self.assertIn("Blue", text)
        self.assertIn("S1. One question", text)
        self.assertNotIn("8.1 A well-posed", text)
        self.assertIn("M1.", prompts.write_rules())

    def test_write_up_prompt_has_no_contest_text(self):
        i = prompts.parse_ideas(idea())[0]
        self.assertNotIn("silver fish", prompts.write_up(i, 4, "7", RECORD))


class Linting(unittest.TestCase):
    def draft(self, answer="7"):
        i = prompts.parse_ideas(idea())[0]
        return drafts.build(i, prompts.parse_write_up(write(answer)), answer, INPUT, 4, config.ANSWER_5_3, "t")

    def i(self, **kw):
        return prompts.parse_ideas(idea(**kw))[0]

    def test_clean_draft_passes(self):
        self.assertIsNone(drafts.lint(self.draft()))
        self.assertIsNone(drafts.lint_idea(self.i()))
        self.assertIsNone(drafts.lint_key(self.i(), "7"))

    def test_key_rules(self):
        self.assertIn("A6", drafts.lint_key(self.i(), "99"))
        self.assertIn("A6", drafts.lint_key(self.i(), "1"))
        self.assertIn("A1", drafts.lint_key(self.i(), "1234"))
        self.assertIn("A1", drafts.lint_key(self.i(), "2/3"))

    def test_topic_is_held(self):
        i = self.i()
        self.assertEqual(drafts.idea_checks({**i, "topic": "G"}, INPUT, None, 0.87)[0], "topic")
        self.assertIn("number theory", prompts.ideas(INPUT, 4, ["transplant"]))
        self.assertIn("CALIBRATING 5 KYU", prompts.ideas(INPUT, 5, ["transplant"]))
        self.assertNotIn("CALIBRATING 5 KYU", prompts.ideas(INPUT, 4, ["transplant"]))

    def test_no_picture_outside_geometry(self):
        d = self.draft()
        d["solution"] = "From the diagram it is clear.\n\n" + d["solution"]
        self.assertIsNotNone(drafts.PICTURE.search(d["solution"]))

    def test_unknown_tag(self):
        d = self.draft()
        d["subtopics"] = ["not-a-technique"]
        self.assertIn("M5", drafts.lint(d))

    def test_missing_why_line(self):
        d = self.draft()
        d["solution"] = "The answer is $7$."
        self.assertIn("M4", drafts.lint(d))

    def test_math_asterisk(self):
        self.assertIn("S9", drafts.lint_idea(self.i(statement="How many integers $n$ satisfy $2*n < 9$ with $n$ positive?")))

    def test_function_of_a_is_not_a_second_part(self):
        self.assertIsNone(drafts.lint_idea(self.i(statement="For a function with $f(a) + f(b) = 3$, how many positive integers $n$ below $9$ work?")))

    def test_leak_finds_copied_wording(self):
        d = self.draft()
        self.assertIsNone(drafts.leak(d, INPUT))
        d["hints"] = ["holds exactly seventeen silver fish and twenty three golden fish"]
        self.assertIn("hint", drafts.leak(d, INPUT))

    def test_stock_phrases_are_not_leaks(self):
        stock = "Find the remainder when N is divided by 1000 please."
        source = inputs.Input("S", RECORD, "Count the odd squares here. " + stock, "")
        d = dict(title="t", statement="Let M be a big number. Find the remainder when M is divided by 1000 please.")
        self.assertIn("statement", drafts.leak(d, source))
        drafts.learn_stock_phrases([stock] * 3)
        self.addCleanup(drafts._stock.clear)
        self.assertIsNone(drafts.leak(d, source))

    def test_tidy_latex(self):
        t = drafts.tidy_latex("So $\\dfrac{a}{b} \\leq 1$ and $$\\frac{a}{b} \\geq 0.$$")
        self.assertEqual(t, "So $\\frac{a}{b} \\le 1$ and $$\\dfrac{a}{b} \\ge 0.$$")

    def test_program_prints_the_key_for_free(self):
        self.assertEqual(drafts.run_program(PROGRAM), ("7", None))
        self.assertIn("rejected", drafts.run_program("import os\nprint(1)")[1])


class Choosing(unittest.TestCase):
    def test_recipes_are_distinct_and_route_needs_two_paths(self):
        one_path = {**RECORD, "solution_paths": RECORD["solution_paths"][:1]}
        self.assertNotIn("change-route", recipes.suitable(one_path))
        self.assertIn("change-route", recipes.suitable(RECORD))
        got = recipes.pick(RECORD, random.Random(1), 3)
        self.assertEqual(len(set(got)), 3)

    def test_partner_is_rare_and_new(self):
        rows = [RECORD] + [dict(kyu=4, techniques=["crt", "pell"]) for _ in range(3)] + [dict(kyu=4, techniques=["dirichlet", "other"]) for _ in range(3)]
        self.assertIn(recipes.rare_partner(RECORD, rows, random.Random(1)), ("dirichlet", "other"))

    def test_sample_spreads_topics_and_families(self):
        rows = []
        for kyu in (5, 4, 3):
            for t in "ACGN":
                for i in range(12):
                    rows.append(dict(id=f"{kyu}{t}{i}", kyu=kyu, topic=t, techniques=[f"{kyu}{t}{i % 6}"], generation_potential="high", figure_needed=False))
        rows.append(dict(id="low", kyu=5, topic="A", techniques=["z"], generation_potential="low", figure_needed=False))
        p = plan.sample(rows)
        self.assertEqual(len(p["inputs"]), 30)
        self.assertNotIn("low", [x["id"] for x in p["inputs"]])
        for kyu in (5, 4, 3):
            topics = [x["topic"] for x in p["inputs"] if x["kyu"] == kyu]
            self.assertEqual(sorted(set(topics)), list("ACGN"))
            self.assertEqual(len(topics), 10)
        self.assertEqual(p, plan.sample(rows))


class FullPlan(unittest.TestCase):
    def rows(self):
        out = []
        for kyu in (5, 4, 3):
            for t in "ACN":
                for i in range(12):
                    out.append(dict(id=f"{kyu}{t}{i}", kyu=kyu, topic=t, family=f"{kyu}{t}{i % 4}", techniques=["x"], generation_potential="high", figure_needed=False))
        return out

    def test_families_take_turns_and_cells_stay_level(self):
        p = plan.full(self.rows(), set(), {}, set(), per_cell=4, expected_pass=1)
        cell = [x["family"] for x in p["inputs"] if x["kyu"] == 5 and x["topic"] == "A"]
        self.assertEqual(len(set(cell)), 4)
        self.assertEqual({x["kyu"] for x in p["inputs"][:9]}, {5, 4, 3})

    def test_counts_what_it_has_and_skips_what_was_used(self):
        p = plan.full(self.rows(), set(), {(5, "A"): 3}, {"5A0"}, per_cell=4, expected_pass=1)
        self.assertEqual(p["cells"]["5A"], 1)
        self.assertNotIn("5A0", [x["id"] for x in p["inputs"]])

    def test_a_thin_cell_goes_round_again_with_new_keys(self):
        p = plan.full([r for r in self.rows() if r["id"] in ("3A0", "3A1")], set(), {}, set(), kyus=(3,), topics="A", per_cell=3, expected_pass=1)
        keys = [x["key"] for x in p["inputs"]]
        self.assertEqual(len(set(keys)), 3)
        self.assertEqual(sum("#2" in k for k in keys), 1)

    def test_pictures_wait_for_diagrams(self):
        r = dict(topic="N", techniques=["t"], core_idea="", crux="")
        self.assertFalse(plan.needs_a_figure(r, {"g"}))
        self.assertTrue(plan.needs_a_figure({**r, "techniques": ["g"]}, {"g"}))
        self.assertTrue(plan.needs_a_figure({**r, "crux": "Draw a sketch of it"}, {"g"}))
        self.assertTrue(plan.needs_a_figure({**r, "topic": "G"}, {"g"}))


class Decisions(unittest.TestCase):
    def test_difficulty_is_data_not_a_failure(self):
        r = gate_report(("difficulty", "investigate", "estimated 6 kyu, target 4 kyu", {}))
        self.assertEqual(run.classify(r)[0], "accept")
        r = gate_report(("blind_solves", "investigate", "too easy for 4 kyu", {}))
        self.assertEqual(run.classify(r)[0], "accept")

    def test_wrong_key_repairs_and_hard_holds(self):
        r = gate_report(("blind_solves", "investigate", "wrong key or ambiguous: 5/7 agree on 8", {"right": 1}))
        self.assertEqual(run.classify(r)[0], "repair")
        r = gate_report(("blind_solves", "investigate", "only 2/7 reach the key and no majority agrees", {"right": 2}))
        self.assertEqual(run.classify(r)[0], "hold")
        r = gate_report(("blind_solves", "investigate", "only 1/7 reach the key and no majority agrees", {"right": 1}))
        self.assertEqual(run.classify(r)[0], "repair")

    def test_fail_and_error(self):
        self.assertEqual(run.classify(gate_report(("well_posedness", "fail", "bad", {})))[0], "repair")
        self.assertEqual(run.classify(gate_report(("backend", "error", "boom", {})))[0], "error")


class Flow(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.patches = [mock.patch.object(run, "PENDING", self.root / "pending"), mock.patch.object(run, "HELD", self.root / "held"),
                        mock.patch.object(drafts, "PENDING", self.root / "pending"), mock.patch.object(drafts, "HELD", self.root / "held"),
                        mock.patch.object(run, "private_dir", lambda: self.root / "private")]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        drafts._taken.clear()
        self.index = originality.Index([dict(id="OTHER", text="an unrelated sentence about nothing much", source="bank")])

    def ctx(self, backend):
        return dict(profile=config.ANSWER_5_3, backend=backend, run="t", records=[RECORD], index=self.index, digest="", thresholds={}, threshold=0.87)

    def test_keeps_the_most_interesting_clean_candidate_and_saves_privately(self):
        ideas = idea(title="Dull", interest=3) + idea(title="Sparkling", interest=9) + idea(title="Broken", interest=10, program="print(sum(range(2)))")
        backend = Scripted([ideas, write()])
        ok = gate_report(("difficulty", "investigate", "estimated 6 kyu, target 4 kyu", {"estimated_kyu": 6}))
        with mock.patch.object(run.gate, "verify", return_value=ok) as v:
            log = run.make_one(INPUT, self.ctx(backend), 1)
        self.assertEqual(log["outcome"], "accept")
        self.assertEqual(log["id"], "sparkling")
        d = v.call_args[0][0]
        self.assertEqual((d["inspired_by"], d["answer"]), ("SRC-1", "7"))
        saved = json.loads((self.root / "pending" / "sparkling.json").read_text(encoding="utf-8"))
        self.assertEqual(set(saved), {"draft", "report"})
        self.assertFalse(backend.calls[0]["cacheable"], "a prompt holding contest text must not be cached")
        row = json.loads((self.root / "private" / "generated_map.jsonl").read_text(encoding="utf-8"))
        self.assertEqual((row["id"], row["inspired_by"]), ("sparkling", "SRC-1"))

    def test_repairs_twice_then_discards_and_logs_why(self):
        backend = Scripted([idea(), write(), idea(), write(), idea(), write()])
        bad = gate_report(("well_posedness", "fail", "pairs may be ordered", {}))
        with mock.patch.object(run.gate, "verify", return_value=bad) as v:
            log = run.make_one(INPUT, self.ctx(backend), 1)
        self.assertEqual(log["outcome"], "discard")
        self.assertEqual(v.call_count, 3)
        self.assertIn("pairs may be ordered", backend.calls[2]["prompt"])
        self.assertIn("pairs may be ordered", log["reason"])
        self.assertFalse((self.root / "pending").exists())

    def test_an_audit_failure_repairs_only_the_write_up(self):
        backend = Scripted([idea(), write(), write()])
        bad, ok = gate_report(("solution_audit", "fail", "a leap in step two", {})), gate_report(("difficulty", "pass", "fine", {}))
        with mock.patch.object(run.gate, "verify", side_effect=[bad, ok]):
            log = run.make_one(INPUT, self.ctx(backend), 1)
        self.assertEqual(log["outcome"], "accept")
        self.assertEqual([c["role"] for c in backend.calls], ["ideas", "write", "write"])
        self.assertIn("a leap in step two", backend.calls[2]["prompt"])

    def test_a_bad_key_costs_no_write_up(self):
        backend = Scripted([idea(program="print(sum(range(2)))"), idea(), write()])
        ok = gate_report(("difficulty", "pass", "fine", {}))
        with mock.patch.object(run.gate, "verify", return_value=ok) as v:
            log = run.make_one(INPUT, self.ctx(backend), 1)
        self.assertEqual(v.call_count, 1)
        self.assertEqual(log["attempts"][0]["step"], "ideas")
        self.assertIn("A6", backend.calls[1]["prompt"])
        self.assertEqual([c["role"] for c in backend.calls], ["ideas", "ideas", "write"])

    def test_the_writer_can_refuse(self):
        backend = Scripted([idea(), "<disagree>the program miscounts</disagree>", idea(), write()])
        ok = gate_report(("difficulty", "pass", "fine", {}))
        with mock.patch.object(run.gate, "verify", return_value=ok) as v:
            log = run.make_one(INPUT, self.ctx(backend), 1)
        self.assertEqual(v.call_count, 1)
        self.assertEqual(log["attempts"][0]["step"], "disagree")
        self.assertIn("the program miscounts", backend.calls[2]["prompt"])

    def test_unreadable_reply_generates_again(self):
        backend = Scripted(["no tags at all", idea(), write()])
        ok = gate_report(("difficulty", "pass", "fine", {}))
        with mock.patch.object(run.gate, "verify", return_value=ok):
            log = run.make_one(INPUT, self.ctx(backend), 1)
        self.assertEqual(log["attempts"][1]["kind"], "ideas")
        self.assertEqual(log["outcome"], "accept")

    def test_plan_limit_stops_the_batch_and_a_rerun_resumes(self):
        backend = Scripted([idea(), write()])
        hit = gate_report(("backend", "error", "plan limit: x", {}))
        hit["plan_limit"] = True
        with mock.patch.object(run.gate, "verify", return_value=hit):
            rows, stopped = run.run_inputs([INPUT], self.ctx(backend), 1, 1)
        self.assertTrue(stopped)
        self.assertEqual(rows[0]["outcome"], "plan_limit")
        self.assertEqual(run.done_inputs("t"), set())

    def test_report_counts_steps_and_cost(self):
        backend = Scripted([idea(program="print(sum(range(2)))") + idea(title="Second"), write()])
        ok = gate_report(("program_judge", "pass", "ok", {}), ("difficulty", "investigate", "estimated 6 kyu, target 4 kyu", {"estimated_kyu": 6}))
        with mock.patch.object(run.gate, "verify", return_value=ok):
            run.run_inputs([INPUT], self.ctx(backend), 1, 1)
        s = report.summary(report.load("t"))
        self.assertEqual(s["steps"]["key"], dict(reached=2, passed=1, investigate=0))
        self.assertEqual(s["steps"]["program_judge"]["passed"], 1)
        self.assertEqual(s["usd_per_passing"], 0.75)
        self.assertEqual(s["difficulty_estimates"], {"4 kyu target, 6 kyu estimated": 1})


if __name__ == "__main__":
    unittest.main()
