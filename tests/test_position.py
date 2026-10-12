"""Execute the real bone+fallback functions with mocked Ashita memory."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'targetarrow.lua').read_text(encoding='utf8')

class PlacementTests(unittest.TestCase):
    def test_bone_first_then_fallback(self):
        executable = next((shutil.which(n) for n in ('lua5.1','luajit','lua','texlua') if shutil.which(n)), None)
        if not executable: self.skipTest('Lua interpreter unavailable')
        start = SOURCE.index('local function pointer_ok(value)')
        end = SOURCE.index('-- Convert 3D world coordinates',start)
        code = SOURCE[start:end]
        fixture = r"""
local settings = {height=1.9}
local words, shorts, floats = {}, {}, {}
local ashita={memory={}}
function ashita.memory.read_uint32(a) return words[a] or 0 end
function ashita.memory.read_uint16(a) return shorts[a] or 0 end
function ashita.memory.read_float(a) return floats[a] or 0 end
local actor=0x120000
local base=0x130000
local link=0x140000
local skeleton=0x150000
words[actor+0x6B8]=base
words[base+0x0C]=link
words[link]=skeleton
shorts[skeleton+0x32]=10
floats[actor+0x678]=14
floats[actor+0x680]=2
floats[actor+0x67C]=6
local offset=skeleton+0x30+4+0x1E*10+4+2*0x1A+0x0E
floats[offset]=1.5
floats[offset+8]=3.25
floats[offset+4]=0.5
local entity={}
function entity:GetType(i) return 2 end
function entity:GetActorPointer(i) return actor end
function entity:GetRenderFlags0(i) return 1 end
function entity:GetLocalPositionX(i) return 99 end
function entity:GetLocalPositionY(i) return 99 end
function entity:GetLocalPositionZ(i) return 99 end
function entity:GetLastPositionX(i) return 88 end
function entity:GetLastPositionY(i) return 88 end
function entity:GetLastPositionZ(i) return 88 end
"""
        assertions = r"""
local x,y,z,anchor = target_anchor(entity,3)
assert(anchor == 'nameplate-bone')
assert(x == 15.5 and y == 5.25 and z == 6.5, x .. ',' .. y .. ',' .. z)
assert(not (x == 99 or y == 100.9), 'wrongly chose hitbox position')
-- A failed skeleton should gracefully take the ordinary entity fallback.
words[actor+0x6B8]=0
x,y,z,anchor = target_anchor(entity,3)
assert(anchor == 'entity-fallback')
assert(x == 99 and y == 100.9 and z == 99)
print('bone-first placement passed')
"""
        with tempfile.TemporaryDirectory() as tmp:
            test = Path(tmp) / 'placement.lua'
            test.write_text(fixture + code + assertions,encoding='utf8')
            result = subprocess.run([executable,str(test)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_nameplate_visibility_independent(self):
        self.assertNotIn('GetNameplateVisibility', SOURCE)
        self.assertIn("return x, y, z, 'nameplate-bone'",SOURCE)
        self.assertLess(SOURCE.index('local wx, wy, wz, anchor_kind = target_anchor('),SOURCE.index('project_world(wx, wy, wz,'))
        self.assertNotIn('position_candidates(', SOURCE)

if __name__ == '__main__': unittest.main()
