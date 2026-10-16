import contextlib
import io
import json
import tempfile
import unittest

from common.bench import load, run
from common.prompt import pick, read


QUESTIONS = {
    "category": {"type": "choice", "criteria": {"interested": "", "out_of_office": ""}},
    "intent": {"type": "score", "criteria": ["none: no interest", "ready: meeting agreed"]},
    "opt_out": {"type": "noul"},
}


class PromptTests(unittest.TestCase):
    def test_label_formatting(self):
        for value in ("out_of_office", "Out of office", " OUT-OF-OFFICE "):
            with self.subTest(value=value):
                self.assertEqual(pick(value, ["interested", "out_of_office"]), "out_of_office")
        self.assertEqual(pick("none", ["none", "ready"]), "none")

    def test_missing_and_non_string_labels_are_rejected(self):
        for value in (None, "", "  ", False, 0, [], {}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    pick(value, ["none", "ready"])

    def test_partial_and_unknown_labels_are_rejected(self):
        for value in ("r", "re", "read", "ready_to_buy", "none of these", "unknown"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    pick(value, ["none", "ready", "review"])

    def test_complete_answers(self):
        answers = {"category": "Out of office", "intent": "None", "opt_out": 0.1}
        self.assertEqual(read(answers, QUESTIONS),
                         {"category": "out_of_office", "intent": "none", "opt_out": 0.1})

    def test_missing_choice_or_score_is_rejected(self):
        for field in ("category", "intent"):
            with self.subTest(field=field):
                answers = {"category": "interested", "intent": "ready", "opt_out": 0.0}
                del answers[field]
                with self.assertRaises(ValueError):
                    read(answers, QUESTIONS)

    def test_invalid_answer_is_recorded_as_a_failed_request(self):
        items = [{"id": "missing", "answer": None}, {"id": "valid", "answer": "ready"}]

        def step(chunk):
            item = chunk[0]
            return {item["id"]: {"intent": pick(item["answer"], ["none", "ready"])}}, []

        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            path = run("labels", items, step, directory)
            records = [json.loads(line) for line in path.read_text().splitlines()]
            labels, _, failed = load(path)

        self.assertEqual(failed, ["missing"])
        self.assertEqual(labels, {"valid": {"intent": "ready"}})
        self.assertEqual(records[1]["labels"], {})
        self.assertTrue(records[1]["error"].startswith("ValueError:"))


if __name__ == "__main__":
    unittest.main()
