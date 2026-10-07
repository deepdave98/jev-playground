import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from reactivation import build_queue, decide, prepare, questions

TODAY = "2026-10-07"


class ReactivationTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / "data/deals.jsonl").read_text().splitlines()[0])

    def queue(self, records, labels=None):
        return build_queue(records, TODAY, lambda *_: labels or {"blocker": "cleared", "evidence": "u1"})

    def test_full_export_validated_before_calls(self):
        bad = {**self.record, "id": "bad", "opt_out": "false"}
        def unexpected(*_):
            self.fail("API called before input validation finished")
        with self.assertRaises(ValueError):
            build_queue([self.record, bad], TODAY, unexpected)

    def test_missing_crm_flag_is_rejected(self):
        del self.record["open_opportunity"]
        with self.assertRaises(ValueError):
            self.queue([self.record])

    def test_future_and_pre_loss_releases_are_excluded(self):
        for published in ("2026-10-08", "2026-07-01", "2026-06-30"):
            with self.subTest(published=published):
                self.record["updates"][0]["published_on"] = published
                self.assertEqual(prepare(self.record, TODAY)[1], "no_recent_release")

    def test_ninety_day_window_is_inclusive(self):
        self.record["lost_on"] = "2026-01-01"
        self.record["updates"][0]["published_on"] = "2026-07-09"
        self.assertIsNotNone(prepare(self.record, TODAY)[0])
        self.record["updates"][0]["published_on"] = "2026-07-08"
        self.assertEqual(prepare(self.record, TODAY)[1], "no_recent_release")

    def test_thirty_day_contact_boundary(self):
        self.record["last_contacted_on"] = "2026-09-07"
        self.assertEqual(len(self.queue([self.record])["queue"]), 1)
        self.record["last_contacted_on"] = "2026-09-08"
        self.assertEqual(self.queue([self.record])["queue"], [])

    def test_account_exclusion_overrides_another_opportunity(self):
        for key in ("customer", "open_opportunity", "opt_out", "last_contacted_on"):
            with self.subTest(key=key):
                blocked = {**self.record, "id": "other", key: "2026-10-01" if key == "last_contacted_on" else True}
                def unexpected(*_):
                    self.fail("suppressed account reached the model")
                self.assertEqual(build_queue([self.record, blocked], TODAY, unexpected)["queue"], [])

    def test_one_candidate_per_account(self):
        duplicate = {**self.record, "id": "other"}
        result = self.queue([self.record, duplicate])
        self.assertEqual(len(result["queue"]), 1)
        self.assertEqual(result["decisions"][1]["reason"], "duplicate_account")

    def test_bad_evidence_never_enters_queue(self):
        for labels in ({"blocker": "cleared", "evidence": "made-up"},
                       {"blocker": "cleared", "evidence": "none"},
                       {"blocker": "unchanged", "evidence": "u1"},
                       {"blocker": "cleared"}, None):
            with self.subTest(labels=labels):
                result = decide(self.record, TODAY, labels)
                self.assertNotEqual(result["reason"], "blocker_cleared")
                self.assertEqual(result["action"], "review")

    def test_model_failure_remains_visible(self):
        def fail(*_):
            raise TimeoutError("upstream timeout")
        result = build_queue([self.record], TODAY, fail)
        self.assertEqual(result["queue"], [])
        self.assertEqual(result["decisions"][0]["reason"], "model_error")

    def test_payload_has_only_loss_reason_and_release_evidence(self):
        self.record["expected"] = {"blocker": "cleared"}
        self.record["email"] = "private@example.com"
        state, _ = prepare(self.record, TODAY)
        self.assertEqual(set(state), {"loss_reason", "updates"})
        self.assertEqual(set(questions(state)["evidence"]["criteria"]), {"none", "u1"})

    def test_queue_preserves_source_text_and_input(self):
        before = copy.deepcopy(self.record)
        item = self.queue([self.record])["queue"][0]
        self.assertEqual(item["evidence"], self.record["updates"][0])
        self.assertEqual(item["loss_reason"], self.record["loss_reason"])
        self.assertEqual(item["action"], "review")
        self.assertEqual(self.record, before)

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            self.queue([self.record, self.record])
        self.record["updates"] *= 2
        with self.assertRaises(ValueError):
            self.queue([self.record])

    def test_non_iso_dates_and_future_contact_are_rejected(self):
        for key, value in (("lost_on", "2026-1-01"), ("last_contacted_on", "2026-10-08")):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    prepare({**self.record, key: value}, TODAY)


if __name__ == "__main__":
    unittest.main()
