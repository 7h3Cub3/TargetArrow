"""Execute TargetArrow's real ImGui panel with a lightweight Ashita UI mock."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'targetarrow.lua').read_text()

class GuiRuntimeTests(unittest.TestCase):
    def test_config_window_and_bobbing_toggle(self):
        interpreter=next((shutil.which(x) for x in ('lua5.1','lua','luajit','texlua') if shutil.which(x)),None)
        if not interpreter: self.skipTest('Lua interpreter not installed')
        code=SOURCE[SOURCE.index('local function draw_config()'):SOURCE.index('-- User commands and event handlers')]
        fixture=r'''
local COLOR_LABELS='Original\0Red\0Blue\0Green\0Gold\0Purple\0Cyan\0White\0Custom\0\0'
local bounds={scale={0.5,2.5},offset={-100,150},height={0,15},bob_speed={0.1,5},bob_distance={0,30},flash_speed={0.1,5},flash_strength={0,0.85}}
local ui={open={true}}
local settings={enabled=true,scale=1,offset=4,height=1.9,bob=0,bob_speed=1.3,bob_distance=5,flash=0,flash_speed=1.5,flash_strength=.45,target_color=0,sub_color=0}
local guard={reason='HideParty loaded; both frames hidden'}
local draw={stage='draw submitted'}
local ImGuiCond_FirstUseEver=4
local writes=0
local function write_settings() writes=writes+1 end
local imgui={}
function imgui.SetNextWindowSize(...) end
function imgui.Begin(...) return true end
function imgui.Text(...) end
function imgui.TextWrapped(...) end
function imgui.Separator(...) end
function imgui.SliderFloat(...) return false end
function imgui.Combo(...) return false end
function imgui.Button(...) return false end
function imgui.End(...) end
function imgui.SameLine(...) end
function imgui.Checkbox(label, ref)
  if label=='Bobbing - gentle up and down' then ref[1]=true;return true end
  return false
end
'''
        tail=r'''
draw_config()
assert(settings.bob==1 and settings.flash==0, 'UI bob did not turn on independently')
assert(writes==1, 'UI settings change was not saved')
assert(ui.open[1]==true)
print('ImGui config test passed')
'''
        with tempfile.TemporaryDirectory() as d:
            script=Path(d)/'ui.lua';script.write_text(fixture+code+tail)
            result=subprocess.run([interpreter,str(script)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)

if __name__=='__main__':unittest.main()
