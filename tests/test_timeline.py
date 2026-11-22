"""Tests for Timeline. Standard library only, like the renderer itself."""

import math
import pathlib
import random
import re
import struct
import sys
import unittest
import zlib
from datetime import date, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import timeline
from timeline import band, render, sprites, themes, wave
from timeline.options import Options
from timeline.source import _group_into_weeks


def sample_year(seed=7, weeks=52):
    rng = random.Random(seed)
    return [max(0, int(30 + 25 * math.sin(i / 6) + rng.gauss(0, 7))) for i in range(weeks)]


class TestWave(unittest.TestCase):
    def test_normalised_range(self):
        w = wave.from_totals(sample_year(), 220)
        self.assertEqual(len(w), 220)
        self.assertAlmostEqual(min(w), 0.0)
        self.assertAlmostEqual(max(w), 1.0)

    def test_loop_has_no_seam(self):
        """The join between the last week and the first must not read as a step."""
        w = wave.from_totals(sample_year(), 220)
        steps = [abs(w[i] - w[i - 1]) for i in range(1, len(w))]
        self.assertLessEqual(abs(w[-1] - w[0]), max(steps),
                             "the wrap is a bigger jump than any step inside the loop")

    def test_rejects_unusable_input(self):
        self.assertIsNone(wave.from_totals([], 220))
        self.assertIsNone(wave.from_totals([5] * 52, 220), "a flat year cannot make a wave")
        self.assertIsNone(wave.from_totals([1, 2, 3], 220), "too few weeks")

    def test_smoothing_calms_the_water(self):
        rough = wave.from_totals(sample_year(), 220, smooth=0.3)
        calm = wave.from_totals(sample_year(), 220, smooth=4.0)
        var = lambda v: sum(abs(v[i] - v[i - 1]) for i in range(1, len(v)))
        self.assertLess(var(calm), var(rough))

    def test_fallbacks(self):
        self.assertEqual(len(wave.sine(100)), 100)
        self.assertEqual(set(wave.flat(10)), {0.5})


class TestPng(unittest.TestCase):
    def build(self, cols=220, rows=35, cell=4):
        w = wave.from_totals(sample_year(), cols)
        field, cores = band.intensity(w, rows)
        return band.render_png(field, cols, rows, cell, themes.resolve("ember")), cores

    def test_is_a_valid_png(self):
        raw, _ = self.build()
        self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
        width, height, depth, colour = struct.unpack(">IIBB", raw[16:26])
        self.assertEqual((width, height), (220 * 4 * 2, 35 * 4))
        self.assertEqual((depth, colour), (8, 3), "8-bit indexed colour")

    def test_chunk_crcs_are_right(self):
        raw, _ = self.build(cols=60, rows=20)
        pos, seen = 8, []
        while pos < len(raw):
            length = struct.unpack(">I", raw[pos:pos + 4])[0]
            tag = raw[pos + 4:pos + 8]
            data = raw[pos + 8:pos + 8 + length]
            crc = struct.unpack(">I", raw[pos + 8 + length:pos + 12 + length])[0]
            self.assertEqual(crc, zlib.crc32(tag + data) & 0xFFFFFFFF, f"bad CRC on {tag}")
            seen.append(tag)
            pos += 12 + length
        self.assertEqual(seen, [b"IHDR", b"PLTE", b"IDAT", b"IEND"])

    def test_tiles_seamlessly(self):
        """The two halves must be identical, or the scroll would stutter at the wrap."""
        cols, rows, cell = 60, 20, 4
        w = wave.from_totals(sample_year(), cols)
        field, _ = band.intensity(w, rows)
        raw = band.render_png(field, cols, rows, cell, themes.resolve("ember"))
        pos, idat = 8, b""
        while pos < len(raw):
            length = struct.unpack(">I", raw[pos:pos + 4])[0]
            if raw[pos + 4:pos + 8] == b"IDAT":
                idat = raw[pos + 8:pos + 8 + length]
            pos += 12 + length
        decoded = zlib.decompress(idat)
        stride = cols * cell * 2 + 1
        for r in range(rows * cell):
            line = decoded[r * stride + 1:(r + 1) * stride]
            self.assertEqual(line[:cols * cell], line[cols * cell:], f"row {r} does not tile")

    def test_ridge_sits_where_the_original_put_it(self):
        _, cores = self.build()
        self.assertEqual((min(cores), max(cores)), (7, 22))


class TestOptions(unittest.TestCase):
    def test_defaults_match_the_original_header(self):
        o = Options({"user": "PasinduSuraweera"})
        self.assertEqual((o.px_width, o.px_height), (880, 140))
        self.assertEqual((o.cols, o.rows, o.cell), (220, 35, 4))

    def test_aliases(self):
        o = Options({"username": "x", "color": "0af", "duration": "10", "sprite": "sail"})
        self.assertEqual(o.user, "x")
        self.assertEqual(o.rider, "sail")
        self.assertEqual(o.speed, 10.0)

    def test_hostile_input_is_neutralised(self):
        o = Options({"user": '"><script>alert(1)</script>', "theme": "../../etc",
                     "rider": "'; DROP", "width": "9e9", "cell": "-5"})
        self.assertIsNone(o.user)
        self.assertTrue(o.user_invalid)
        self.assertEqual(o.theme, "ember")
        self.assertEqual(o.rider, "surfer")
        self.assertLessEqual(o.px_width, 1600)
        self.assertGreaterEqual(o.cell, 2)

    def test_clamping(self):
        self.assertEqual(Options({"weeks": "999"}).weeks, 53)
        self.assertEqual(Options({"speed": "0.001"}).speed, 4.0)
        self.assertEqual(Options({"smooth": "abc"}).smooth, 1.0)

    def test_round_trip_query(self):
        o = Options({"user": "a", "theme": "ice", "rider": "flag", "width": "600"})
        again = Options(dict(p.split("=", 1) for p in o.to_query().split("&")))
        self.assertEqual((again.theme, again.rider, again.px_width), ("ice", "flag", 600))


class TestThemes(unittest.TestCase):
    def test_hex_parsing_rejects_anything_else(self):
        self.assertEqual(themes.parse_hex("#FF6A3D"), "#ff6a3d")
        self.assertEqual(themes.parse_hex("0af"), "#00aaff")
        for bad in ('red" onload="x', "#12", "javascript:alert(1)", "", None, "#1234567"):
            self.assertIsNone(themes.parse_hex(bad), f"{bad!r} should not parse")

    def test_accent_alone_derives_the_rest(self):
        dark = themes.resolve("ember", accent="#3366ff")
        light = themes.resolve("paper", accent="#3366ff")
        self.assertGreater(themes.luma(dark["hot"]), themes.luma(dark["accent"]))
        self.assertLess(themes.luma(light["hot"]), themes.luma(light["accent"]))


class TestRender(unittest.TestCase):
    def test_every_theme_and_rider_renders(self):
        for theme in themes.THEMES:
            for rider in sprites.SPRITES:
                svg, meta = timeline.generate({"theme": theme, "rider": rider, "width": "400"})
                self.assertTrue(svg.startswith("<svg"))
                self.assertTrue(svg.rstrip().endswith("</svg>"))
                self.assertEqual(meta["theme"], theme)

    def test_no_user_input_reaches_the_markup(self):
        payload = '"><script>alert(1)</script>'
        out = timeline.error_svg(payload)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_escaping(self):
        self.assertEqual(render.esc('<a href="x">&'), "&lt;a href=&quot;x&quot;&gt;&amp;")

    def test_reduced_motion_is_honoured(self):
        svg, _ = timeline.generate({"width": "400"})
        self.assertIn("prefers-reduced-motion", svg)

    def test_rider_stays_inside_the_band(self):
        """Pushed to the far right, the figure must still be fully drawn on the band.

        Only the rider group is measured: the sparkle layer lives on the doubled
        tape, so its coordinates legitimately run to twice the width.
        """
        for at in ("0", "50", "100"):
            svg, _ = timeline.generate({"width": "400", "rider_at": at})
            group = re.search(r'<g class="rd">(.*?)</g>', svg, re.S)
            self.assertIsNotNone(group, "no rider group was emitted")
            right = [int(x) + int(w) for x, w in
                     re.findall(r'<rect x="(\d+)" y="\d+" width="(\d+)"', group.group(1))]
            self.assertLessEqual(max(right), 400, f"rider_at={at} ran past the right edge")
            self.assertGreaterEqual(min(right), 0)

    def test_switches_actually_switch(self):
        with_glints, _ = timeline.generate({"width": "400", "glints": "1"})
        without, _ = timeline.generate({"width": "400", "glints": "0"})
        self.assertIn("gleam", with_glints)
        self.assertNotIn("gleam", without)
        self.assertIn("stroke=", timeline.generate({"width": "400", "border": "1"})[0])


class TestWeekGrouping(unittest.TestCase):
    def test_full_year(self):
        start = date(2025, 11, 23)
        days = [((start + timedelta(days=i)).isoformat(), i % 9) for i in range(364)]
        self.assertEqual(len(_group_into_weeks(days)), 52)

    def test_partial_ends_are_dropped(self):
        start = date(2025, 11, 23)
        days = [((start + timedelta(days=i)).isoformat(), 1) for i in range(364)]
        self.assertEqual(len(_group_into_weeks(days[3:-2])), 51)

    def test_duplicates_collapse(self):
        start = date(2025, 11, 23)
        days = [((start + timedelta(days=i)).isoformat(), 2) for i in range(14)] * 2
        self.assertEqual(_group_into_weeks(days), [14, 14])


if __name__ == "__main__":
    unittest.main(verbosity=2)
