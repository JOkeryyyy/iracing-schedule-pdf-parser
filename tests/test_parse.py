from pathlib import Path
import unittest

from pdf_schedule_parser.extract import extract_pdf_text
from pdf_schedule_parser.models import ExtractedPage, ParsedSeries, ParserWarning
from pdf_schedule_parser.parse import parse_pages


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_schedule_text.txt"


class ParserModelTests(unittest.TestCase):
    def test_series_defaults_support_manual_review_fields(self):
        series = ParsedSeries(id="series_test", name="Test Series", discipline="oval")

        self.assertIsNone(series.fixed_setup)
        self.assertEqual(series.fixed_setup_source, "unknown")
        self.assertEqual(series.start_type, "unknown")
        self.assertEqual(series.start_type_source, "unknown")

    def test_warning_records_source_location(self):
        warning = ParserWarning("fixedSetupUnknown", "Needs review", page=6, line=12)

        self.assertEqual(warning.code, "fixedSetupUnknown")
        self.assertEqual(warning.page, 6)
        self.assertEqual(warning.line, 12)


class ScheduleParserTests(unittest.TestCase):
    def test_parse_pages_extracts_series_setup_and_weeks(self):
        text = FIXTURE.read_text()
        result = parse_pages([ExtractedPage(page=6, text=text)])

        self.assertEqual(len(result.series), 2)
        mini_stock = result.series[0]

        self.assertEqual(mini_stock.name, "Mini Stock Rookie Series by Thrustmaster")
        self.assertEqual(mini_stock.discipline, "oval")
        self.assertIsNone(mini_stock.fixed_setup)
        self.assertEqual(mini_stock.fixed_setup_source, "unknown")
        self.assertEqual(mini_stock.start_type, "rolling")
        self.assertEqual(mini_stock.start_type_source, "weatherText")
        self.assertEqual(mini_stock.schedule["intervalMinutes"], 30)
        self.assertEqual(mini_stock.schedule["minuteOffsets"], [15, 45])
        self.assertEqual(mini_stock.official, {"minEntries": 6, "splitAt": 14, "drops": 4})
        self.assertEqual(len(mini_stock.weeks), 2)
        self.assertEqual(mini_stock.weeks[0].track_name, "Charlotte Motor Speedway - Oval")
        self.assertEqual(mini_stock.weeks[0].race_length, {"type": "laps", "value": 15})
        self.assertEqual(mini_stock.weeks[0].weather["rainChancePercent"], 0)

    def test_parse_pages_extracts_fixed_setup_from_series_name(self):
        text = FIXTURE.read_text()
        result = parse_pages([ExtractedPage(page=6, text=text)])

        arca = result.series[1]

        self.assertEqual(arca.name, "ARCA Menards Series")
        self.assertTrue(arca.fixed_setup)
        self.assertEqual(arca.fixed_setup_source, "seriesName")
        self.assertEqual(arca.start_type, "standing")
        self.assertEqual(arca.weeks[0].weather["rainChancePercent"], 15)


class PdfExtractorTests(unittest.TestCase):
    def test_extract_pdf_text_rejects_missing_pdf(self):
        with self.assertRaises(FileNotFoundError):
            extract_pdf_text(Path("/tmp/does-not-exist-season-schedule.pdf"))


if __name__ == "__main__":
    unittest.main()
