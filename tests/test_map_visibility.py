"""Tests for hiding the TargetArrow sprite while the native FFXI map is open."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'targetarrow.lua').read_text(encoding='utf-8')

class MapVisibilityTests(unittest.TestCase):
    def test_map_checked_after_hideparty_before_target_or_sprite(self):
        for fragment in ("AshitaCore:GetPointerManager()", "pm:Get('menu')", "ashita.memory.read_string(address + 0x46, 16)", "draw.stage = 'hidden while map is open'", 'map_open=%s'):
            self.assertIn(fragment, SOURCE)
        self.assertLess(SOURCE.index('if not can_show_replacement() then'), SOURCE.index('if map_is_open() then'))
        self.assertLess(SOURCE.index('if map_is_open() then'), SOURCE.index('local entities, index, slot = acquire_target();'))
        self.assertLess(SOURCE.index('if map_is_open() then'), SOURCE.index('sprite:Draw('))

    def test_map_detection_is_read_only(self):
        segment = SOURCE.split('-- Native map occlusion', 1)[1].split('local function can_show_replacement()', 1)[0]
        for forbidden in ('ashita.memory.write_', 'QueueCommand', 'keybd_event'):
            self.assertNotIn(forbidden, segment)

    def test_render_skips_target_acquisition_while_map_open(self):
        interpreter = next((shutil.which(x) for x in ('lua5.1', 'luajit', 'lua', 'texlua') if shutil.which(x)), None)
        if interpreter is None:
            self.skipTest('Lua interpreter unavailable; GitHub CI runs this test')
        start = SOURCE.index('local function draw_frame()')
        end = SOURCE.index('-- ImGui configuration: open using /ta config', start)
        code = SOURCE[start:end]
        fixture = r''' 
local settings = {enabled=true}
local draw = {stage='initial',target_index=0,anchor='none',candidate_count=0}
local guard = {allowed=false}
local opened = true
local calls = 0
local function can_show_replacement() guard.allowed=true;return true end
local function map_is_open() return opened end
local function acquire_target() calls=calls+1;return nil end
'''
        checks = r'''
draw_frame()
assert(draw.stage == 'hidden while map is open')
assert(calls == 0, 'map open should stop before acquiring target')
opened = false
-- Same function, next frame, no cached map flag. Drawing recovers.
draw_frame()
assert(draw.stage == 'no active target')
assert(calls == 1, 'closing map should restore target acquisition')
print('map render suppression tested')
'''
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / 'test.lua'
            script.write_text(fixture + code + checks, encoding='utf-8')
            result = subprocess.run([interpreter, str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + '\n' + result.stderr)

    def test_menu_open_close_via_real_lua_function(self):
        interpreter = next((shutil.which(x) for x in ('lua5.1', 'luajit', 'lua', 'texlua') if shutil.which(x)), None)
        if interpreter is None:
            self.skipTest('Lua interpreter unavailable; GitHub CI runs this test')
        addr_function = SOURCE[SOURCE.index('local function is_32bit_address(value)'):SOURCE.index('local function hideparty_loaded()')]
        menu_function = SOURCE[SOURCE.index('local map_ui ='):SOURCE.index('-- Target acquisition and placement')]
        fixture = r'''
local current_menu = 'nothing'
local good_pointer = true
local words = {[0x123000] = 0x124000, [0x124000] = 0x125000, [0x125004] = 0x126000}
local ashita = {memory = {}}
function ashita.memory.read_uint32(p) return words[p] or 0 end
function ashita.memory.read_string(p, count)
    assert(p == 0x126046 and count == 16, 'incorrect menu name address')
    return current_menu
end
local AshitaCore = {}
function AshitaCore:GetPointerManager()
    if not good_pointer then return nil end
    return {Get=function(self, key) assert(key == 'menu'); return 0x123000 end}
end
'''
        checks = r'''
assert(not map_is_open() and not map_ui.open)
current_menu = 'menu    map   '
assert(map_is_open() and map_ui.open)
current_menu = 'map\0ignored'
assert(map_is_open())
current_menu = 'inventor'
assert(not map_is_open() and not map_ui.open)
good_pointer = false
assert(not map_is_open() and map_ui.menu == 'unavailable')
print('map detection tested')
'''
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / 'test.lua'
            script.write_text(fixture + addr_function + menu_function + checks, encoding='utf-8')
            result = subprocess.run([interpreter, str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + '\n' + result.stderr)

if __name__ == '__main__':
    unittest.main()
