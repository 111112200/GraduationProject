import unittest

from app.services.chunk_service import build_chunks, split_text_with_offsets


class ChunkServiceRegressionTest(unittest.TestCase):
    def test_long_unpunctuated_text_has_a_hard_limit_and_offsets(self):
        text = "中文长文本" * 100
        chunks = split_text_with_offsets(
            text,
            max_tokens=96,
            overlap_tokens=20,
            length_function=len,
        )

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk["token_length"] <= 96 for chunk in chunks))
        self.assertEqual(chunks[0]["start_char"], 0)
        self.assertEqual(chunks[-1]["end_char"], len(text))
        for previous, current in zip(chunks, chunks[1:]):
            self.assertGreater(current["start_char"], previous["start_char"])
            self.assertLessEqual(current["start_char"], previous["end_char"])

    def test_build_chunks_keeps_parent_and_section_metadata(self):
        chunks = build_chunks(
            [
                {
                    "report_id": 7,
                    "block_id": 3,
                    "section_type": "REFLECTION",
                    "section_title": "心得体会",
                    "content": "这是一段足够长的心得体会文本。",
                }
            ],
            report_id=7,
        )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["chunk_id"], "r7_b3_c0")
        self.assertEqual(chunks[0]["block_id"], 3)
        self.assertEqual(chunks[0]["section_type"], "REFLECTION")
        self.assertEqual(chunks[0]["start_char"], 0)
        self.assertEqual(chunks[0]["end_char"], len(chunks[0]["content"]))


if __name__ == "__main__":
    unittest.main()
