"""Run the real Restore Defaults and ImGui callback using a small Lua mock."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'targetarrow.lua').read_text(encoding='utf-8')


class RestoreDefaultsRuntimeTests(unittest.TestCase):
    def test_restore_all_values_and_save_without_touching_guard(self):
        interpreter = next((shutil.which(x) for x in ('lua5.1', 'lua', 'luajit') if shutil.which(x)), None)
        if interpreter is None:
            self.skipTest('Lua interpreter not installed')
        defaults = SOURCE[
            SOURCE.index('local DEFAULT_SETTINGS = {'):
            SOURCE.index("local settings_file = addon.path")
        ]
        restore = SOURCE[
            SOURCE.index('local function restore_defaults()'):
            SOURCE.index('local function rgb_to_u32')
        ]
        config = SOURCE[
            SOURCE.index('local function draw_config()'):
            SOURCE.index('-- User commands and event handlers')
        ]
        setup = r'''
local ui = { open = { true } }
local guard = {reason = 'HideParty loaded; native party and target frames hidden', allowed = true}
local draw = {stage = 'draw submitted'}
local ImGuiCond_FirstUseEver = 4
local COLOR_LABELS = 'Original\0Red\0Blue\0Green\0Gold\0Purple\0Cyan\0White\0Custom\0\0'
local bounds = {scale={0.5,2.5},offset={-100,150},height={0,15},bob_speed={0.1,5},bob_distance={0,30},flash_speed={0.1,5},flash_strength={0,0.85}}
local writes = 0
local saved = {}
local message = nil
local function notify(v) message = v end
local function write_settings()
    writes = writes + 1
    saved = {}
    for k, v in pairs(settings) do saved[k] = v end
end
local imgui = {}
function imgui.SetNextWindowSize(...) end
function imgui.Begin(...) return true end
function imgui.End(...) end
function imgui.Text(...) end
function imgui.TextWrapped(...) end
function imgui.Separator(...) end
function imgui.SliderFloat(...) return false end
function imgui.Combo(...) return false end
function imgui.ColorEdit4(...) return false end
function imgui.Checkbox(...) return false end
function imgui.SameLine(...) end
function imgui.Button(label) return label == 'Restore Defaults' end
'''
        checks = r'''
-- Deliberately change every setting, including values hidden behind UI tabs.
for key, default in pairs(DEFAULT_SETTINGS) do
    if type(default) == 'boolean' then
        settings[key] = not default
    else
        settings[key] = 999
    end
end
local previous_guard = guard
local previous_draw = draw
-- Clicking the Restore Defaults button must invoke the real callback.
draw_config()
for key, default in pairs(DEFAULT_SETTINGS) do
    assert(settings[key] == default, 'Not restored: ' .. key)
    assert(saved[key] == default, 'Not saved: ' .. key)
end
assert(settings.enabled == true and settings.bob == 0 and settings.flash == 0)
assert(settings.scale == 1.0 and settings.offset == 4 and settings.height == 1.9)
assert(settings.target_color == 0 and settings.sub_color == 0)
assert(writes == 1, 'Expected exactly one immediate save')
assert(ui.open[1] == true, 'Restore unexpectedly closed window')
assert(guard == previous_guard and guard.allowed == true, 'HideParty guard changed')
assert(draw == previous_draw and draw.stage == 'draw submitted', 'Render state changed')
assert(message ~= nil, 'No user feedback')
print('Restore Defaults UI test passed')
'''
        # The sections are copied as written from production Lua so the test
        # exercises the actual callback rather than reimplementing its logic.
        script = "local addon={path='test'}\n" + defaults + setup + restore + config + checks
        with tempfile.TemporaryDirectory() as directory:
            test_file = Path(directory) / 'reset_test.lua'
            test_file.write_text(script, encoding='utf-8')
            result = subprocess.run([interpreter, str(test_file)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + '\n' + result.stderr)


if __name__ == '__main__':
    unittest.main()
