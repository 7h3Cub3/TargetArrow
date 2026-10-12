"""Offline safety/metadata regression checks for 7h3Cub3's TargetArrow.

The Lua scenario tests execute the actual dependency+visibility guard extracted
from targetarrow.lua against a mocked Ashita state. They do not claim to
test the in-game Direct3D render pipeline.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'targetarrow.lua').read_text(encoding='utf-8')


class RepositoryTests(unittest.TestCase):
    def test_metadata(self):
        for phrase in (
            "addon.name    = 'targetarrow'",
            "addon.author  = '7h3Cub3'",
            "addon.version = '1.0.0'",
            "addon.link    = 'https://github.com/7h3Cub3/TargetArrow'",
            "AddonManager:IsLoaded('hideparty')",
            'target:GetIsActive(slot)',
        ):
            self.assertIn(phrase, SOURCE)
        self.assertNotIn('target:GetActive(slot)', SOURCE)
        self.assertIn("if target:GetIsActive(slot) == 0 then return nil; end", SOURCE)
        self.assertIn('local wx, wy, wz, anchor_kind = target_anchor(entities, index);', SOURCE)
        self.assertIn("draw.stage = 'draw submitted'", SOURCE)

    def test_guard_runs_before_sprite_draw(self):
        self.assertIn('if not can_show_replacement() then', SOURCE)
        self.assertEqual(SOURCE.count('sprite:Draw('), 1)
        self.assertLess(SOURCE.index('if not can_show_replacement() then'),
                        SOURCE.index('sprite:Draw('))

    def test_guard_does_not_write_native_ui(self):
        section = SOURCE.split('-- HideParty dependency and native visibility interlock', 1)[1].split('-- Target tracking and camera projection', 1)[0]
        self.assertNotIn('ashita.memory.write_', section)
        for value in ('+ 0x69', '+ 0x6A', '+ 0x19', '+ 0x23', "AddonManager:IsLoaded('hideparty')"):
            self.assertIn(value, section)

    def test_third_party_code_not_bundled(self):
        self.assertIn('local function bone_anchor(actor)', SOURCE)
        self.assertIn('0x6B8', SOURCE)
        self.assertNotIn('target:GetArrowPositionX(slot)', SOURCE)
        self.assertNotIn('target:GetIsArrowActive(slot)', SOURCE)

    def test_license_and_assets(self):
        self.assertIn('GNU GENERAL PUBLIC LICENSE', (ROOT / 'LICENSE').read_text())
        self.assertIn('SPDX-License-Identifier: GPL-3.0-or-later', SOURCE)
        for name in ('arrow.png', 'subarrow.png'):
            data = (ROOT / name).read_bytes()
            self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertGreater(len(data), 100)
        for name in ('README.md', 'THIRD_PARTY_NOTICES.md', 'docs/INSTALLATION.md', 'docs/TECHNICAL.md'):
            self.assertIn('TargetArrow', (ROOT / name).read_text(encoding='utf-8'))

    def test_mocked_hideparty_dependency_and_visibility(self):
        executable = next((shutil.which(n) for n in ('lua5.1', 'luajit', 'lua', 'lua5.4', 'texlua') if shutil.which(n)), None)
        if executable is None:
            self.skipTest('Lua runtime unavailable locally; GitHub Actions installs Lua 5.1')
        guard_source = 'local PARTY_TARGET_SIGNATURE =' + SOURCE.split('local PARTY_TARGET_SIGNATURE =', 1)[1].split('-- ==========================================================================', 1)[0]
        preamble = r'''
local loaded = false
local haveManager = true
local haveSignature = true
local partyGlobal = 0x300000
local targetGlobal = 0x400000
local signature = 0x200000
local partyWrapper = 0x500000
local targetWrapper = 0x700000
local partyPrimitive = 0x600000
local targetPrimitive = 0x800000
local data32, data8 = {}, {}
local guard = { reason='not checked', allowed=false, frame=0, next_lookup=0, party_ptr=nil, target_ptr=nil }
local ashita = { memory = {} }
local AddonManager = { IsLoaded = function(self, name)
    assert(name == 'hideparty')
    return loaded
end }
function ashita.memory.find(...) if haveSignature then return signature else return 0 end end
function ashita.memory.read_uint32(addr) return data32[addr] or 0 end
function ashita.memory.read_uint8(addr) return data8[addr] end
data32[signature+0x19], data32[signature+0x23] = partyGlobal, targetGlobal
data32[partyGlobal], data32[partyWrapper+0x08] = partyWrapper, partyPrimitive
data32[targetGlobal], data32[targetWrapper+0x08] = targetWrapper, targetPrimitive
local function visibility(p, visible)
  local v = visible and 1 or 0
  data8[p + 0x69], data8[p + 0x6A] = v, v
end
visibility(partyPrimitive, false)
visibility(targetPrimitive, false)
'''
        cases = r'''
-- Dependency missing: hidden flags are not proof that HideParty is running.
assert(can_show_replacement() == false)
assert(guard.reason == 'HideParty is not loaded')
-- Dependency loaded and both primitives hidden.
loaded = true
assert(can_show_replacement() == true, guard.reason)
-- /hideparty show: both native UI primitives visible.
visibility(partyPrimitive, true)
visibility(targetPrimitive, true)
assert(can_show_replacement() == false)
-- Only the party is hidden: original arrow remains; do not duplicate.
visibility(partyPrimitive, false)
assert(can_show_replacement() == false)
-- Only the target frame is hidden: party still visible; do not draw.
visibility(targetPrimitive, false)
visibility(partyPrimitive, true)
assert(can_show_replacement() == false)
-- Both hidden again: overlay can recover with no reload.
visibility(partyPrimitive, false)
assert(can_show_replacement() == true)
-- Mixed bytes must fail closed.
data8[targetPrimitive+0x6A] = 1
assert(can_show_replacement() == false)
visibility(targetPrimitive, false)
assert(can_show_replacement() == true)
-- The addon can be unloaded while native state remains at 0.
loaded = false
assert(can_show_replacement() == false, 'unloaded HideParty must suppress arrow')
-- Missing AddonManager must also fail closed (no guessing).
AddonManager = nil
assert(can_show_replacement() == false)
-- Read failure / pointer loss must suppress the overlay.
AddonManager = { IsLoaded = function() return true end }
data32[targetGlobal] = 0
assert(can_show_replacement() == false)
data32[targetGlobal] = targetWrapper
assert(can_show_replacement() == true)
print('TargetArrow: HideParty dependency and visibility tests passed')
'''
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / 'guard.lua'
            script.write_text(preamble + guard_source + cases, encoding='utf-8')
            p = subprocess.run([executable, str(script)], text=True, capture_output=True)
            self.assertEqual(p.returncode, 0, p.stdout + '\n' + p.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
