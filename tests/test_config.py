"""Checks that the GUI and coloring effects cannot bypass HideParty or change classic defaults."""
from pathlib import Path
import unittest

R=Path(__file__).resolve().parents[1]
S=(R/'targetarrow.lua').read_text(encoding='utf-8')

class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        for phrase in ('bob = 0,', 'flash = 0,', 'target_color = 0,', 'sub_color = 0,'):
            self.assertIn(phrase, S)
        self.assertIn("settings.bob == 1",S)
        self.assertIn("settings.flash == 1",S)
    def test_original_art_preserved(self):
        self.assertIn("main_texture = open_png('arrow.png')",S)
        self.assertIn("sub_texture = open_png('subarrow.png')",S)
        self.assertIn('tinted and main_neutral or main_texture',S)
        self.assertIn('tinted and sub_neutral or sub_texture',S)
        self.assertIn("if mode == 0 then return 255, 255, 255, false; end",S)
    def test_window_and_commands(self):
        for x in ("require('imgui')", "command == 'config'", 'imgui.Begin(', 'imgui.Checkbox(', 'imgui.Combo(', 'imgui.ColorEdit4(', 'imgui.SliderFloat('):
            self.assertIn(x,S)
        self.assertIn("elseif command == 'bob' or command == 'flash'",S)
    def test_guard_order(self):
        self.assertLess(S.index('if not can_show_replacement() then'),S.index('sprite:Draw('))
        self.assertIn("AddonManager:IsLoaded('hideparty')",S)
    def test_reset_is_in_config_and_persists(self):
        self.assertIn("imgui.Button('Restore Defaults')", S)
        self.assertIn("local DEFAULT_SETTINGS = {", S)
        self.assertIn("local function restore_defaults()", S)
        reset = S.split('local function restore_defaults()', 1)[1].split('local function rgb_to_u32', 1)[0]
        self.assertIn('pairs(DEFAULT_SETTINGS)', reset)
        self.assertIn('settings[key] = value', reset)
        self.assertIn('write_settings()', reset)
        self.assertIn('settings.enabled = enabled[1]', S)
    def test_screenshots(self):
        for path in ('original-hideparty.png','targetarrow.png'):
            self.assertTrue((R/'screenshots'/path).is_file())
            self.assertIn('screenshots/'+path, (R/'README.md').read_text())

if __name__ == '__main__': unittest.main()
