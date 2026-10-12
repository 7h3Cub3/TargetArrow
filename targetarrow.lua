-- SPDX-License-Identifier: GPL-3.0-or-later
--[[
    TargetArrow 1.0.0
    Copyright (C) 2026 7h3Cub3
    https://github.com/7h3Cub3/TargetArrow

    TargetArrow restores only the in-world target pointer when players use the
    stock Ashita 4 HideParty addon to hide the game's party and target UI.

    WHY A SEPARATE ADDON?
    HideParty conceals the native target frame and the original target pointer
    together. A custom UI such as XIUI can replace the target frame, but it
    cannot restore the original in-world pointer. TargetArrow renders its own.

    SAFETY CONTRACT
    Draw only if ALL of the following are currently true:
      1. This addon is enabled.
      2. Ashita's addon manager confirms 'hideparty' is actually loaded.
      3. The native party primitive has both visibility flags cleared.
      4. The native target primitive has both visibility flags cleared.
      5. A selected target has a valid on-screen bone or fallback anchor.
    If any verification fails, draw nothing. The guard never writes memory.

    The HideParty visibility layout and Ashita memory interface are sourced
    from publicly documented Ashita 4 interfaces. Placement uses bone #2 as
    in the previously working TargetArrow 1.0.1, with independent implementation.
    See THIRD_PARTY_NOTICES.md for source acknowledgments.
]]

addon.name    = 'targetarrow'; -- Ashita loads with: /addon load targetarrow
addon.author  = '7h3Cub3';
addon.version = '1.0.0';
addon.desc    = 'In-world target cursor for the original HideParty addon.';
addon.link    = 'https://github.com/7h3Cub3/TargetArrow';

require('common');
local ffi = require('ffi');
local imgui = require('imgui');
local d3d = require('d3d8');
local device = d3d.get_device();
local d3dx = ffi.C;

-- Single source of truth for fresh-install and Restore Defaults values.
-- The session-only enabled flag resets to true when the addon loads.
local DEFAULT_SETTINGS = {
    enabled = true,       -- /ta on|off: session-only; default on after reload
    scale = 1.0,          -- Size of arrow texture, 0.5 to 2.5
    offset = 4,           -- Extra screen pixels above the anchor, -100 to 150
    height = 1.9,         -- Fallback height in world units above model origin
    bob = 0,              -- Optional vertical bobbing, OFF by default
    bob_speed = 1.3,      -- Bobbing cycles per second
    bob_distance = 5.0,   -- Maximum upward/downward movement in pixels
    flash = 0,            -- Optional alpha pulsing, OFF by default
    flash_speed = 1.5,    -- Flash cycles per second
    flash_strength = 0.45,-- How much opacity changes (0.0 to 0.85)
    target_color = 0,     -- 0 = ORIGINAL GOLD, unchanged original PNG
    sub_color = 0,        -- 0 = ORIGINAL GREEN, unchanged original PNG
    target_r = 1.0, target_g = 0.72, target_b = 0.30,
    sub_r = 0.35, sub_g = 1.0, sub_b = 0.65,
};
-- Copy the defaults instead of using them as mutable live settings, so that
-- changes in the UI never change what Restore Defaults means.
local settings = {};
for key, value in pairs(DEFAULT_SETTINGS) do
    settings[key] = value;
end
local settings_file = addon.path .. 'settings.lua';
local WIDTH, HEIGHT = 32, 40;
local source_rect = ffi.new('RECT', { 0, 0, WIDTH, HEIGHT });
local screen_pos = ffi.new('D3DXVECTOR2');
local sprite_scale = ffi.new('D3DXVECTOR2');
local sprite, main_texture, sub_texture = nil, nil, nil;
local main_neutral, sub_neutral = nil, nil;

-- Color option 0 uses the exact original 1.0 artwork. Other choices colorize
-- a neutral copy of the SAME shape; no change to shape, border or alpha mask.
-- Choose 'Custom' (8) to use the RGB ColorEdit controls in /ta config.
local COLOR_LABELS = 'Original\0Red\0Blue\0Green\0Gold\0Purple\0Cyan\0White\0Custom\0\0';
local COLOR_NAMES = { 'original', 'red', 'blue', 'green', 'gold', 'purple', 'cyan', 'white', 'custom' };
local COLORS = {
    [1] = { 255, 72, 72 }, [2] = { 75, 160, 255 }, [3] = { 65, 235, 123 },
    [4] = { 255, 190, 49 }, [5] = { 180, 98, 255 }, [6] = { 45, 230, 255 },
    [7] = { 255, 255, 255 },
};

local ui = { open = { false }, error_reported = false };

local render_error_reported = false;
local last_render_error = 'none';
-- The HideParty guard and the actual drawing pipeline are deliberately separate.
-- A true guard does NOT mean an arrow was drawn; use /ta status to see why.
local draw = {
    stage = 'not started',
    target_index = 0,
    target_slot = 0,
    anchor = 'none',
    successes = 0,
    candidate_count = 0,
};

-- This is the effective visibility status from the most recent draw frame.
-- It is not a persistent permission and is recomputed for every frame.
local guard = {
    reason = 'waiting for first frame',
    allowed = false,
    frame = 0,
    next_lookup = 0,
    party_ptr = nil,
    target_ptr = nil,
};

local function notify(value)
    print('[TargetArrow] ' .. value);
end

local bounds = {
    scale = { 0.5, 2.5 },
    offset = { -100, 150 },
    height = { 0, 15 },
    bob = { 0, 1 }, bob_speed = { 0.1, 5 }, bob_distance = { 0, 30 },
    flash = { 0, 1 }, flash_speed = { 0.1, 5 }, flash_strength = { 0, 0.85 },
    target_color = { 0, 8 }, sub_color = { 0, 8 },
    target_r = { 0, 1 }, target_g = { 0, 1 }, target_b = { 0, 1 },
    sub_r = { 0, 1 }, sub_g = { 0, 1 }, sub_b = { 0, 1 },
};

-- Plain-text values only; intentionally do not execute settings.lua as code.
local function read_settings()
    local file = io.open(settings_file, 'r');
    if file == nil then return; end
    local content = file:read('*a');
    file:close();
    for key, range in pairs(bounds) do
        local raw = content:match('%f[%a]' .. key .. '%s*=%s*([%-%d%.]+)');
        local value = tonumber(raw);
        if value ~= nil and value >= range[1] and value <= range[2] then
            local is_enum = key == 'target_color' or key == 'sub_color' or key == 'bob' or key == 'flash';
            if not is_enum or value == math.floor(value) then
                settings[key] = value;
            end
        end
    end
end

local function write_settings()
    local file = io.open(settings_file, 'w');
    if file == nil then
        notify('Cannot save settings; check folder permissions.');
        return;
    end
    -- Fixed order: readable, stable, and never executes user supplied Lua.
    local keys = {
        'scale', 'offset', 'height', 'bob', 'bob_speed', 'bob_distance',
        'flash', 'flash_speed', 'flash_strength', 'target_color', 'sub_color',
        'target_r', 'target_g', 'target_b', 'sub_r', 'sub_g', 'sub_b'
    };
    for _, key in ipairs(keys) do
        file:write(('%s=%.4f\n'):format(key, settings[key]));
    end
    file:close();
end

-- Reset *every* user-facing value at once, including independent cursor
-- colors, both animation toggles and their speeds, cursor geometry and the
-- session-only enabled flag. Persist the result immediately so an older
-- settings.lua cannot restore custom values after reloading the addon.
-- The HideParty guard and runtime diagnostic state are intentionally untouched.
local function restore_defaults()
    for key, value in pairs(DEFAULT_SETTINGS) do
        settings[key] = value;
    end
    write_settings();
    notify('Original defaults restored (animation OFF).');
end

local function rgb_to_u32(r, g, b, alpha)
    local function component(value)
        return math.max(0, math.min(255, math.floor(value + 0.5)));
    end
    return d3d.D3DCOLOR_ARGB(component(alpha), component(r), component(g), component(b));
end

-- The default returns opaque WHITE, causing the untouched original artwork
-- to be displayed exactly as in the previous in-game working release.
local function color_for(slot)
    local mode = slot == 1 and settings.sub_color or settings.target_color;
    if mode == 0 then return 255, 255, 255, false; end
    if mode == 8 then
        local prefix = slot == 1 and 'sub_' or 'target_';
        return settings[prefix .. 'r'] * 255,
               settings[prefix .. 'g'] * 255,
               settings[prefix .. 'b'] * 255, true;
    end
    local color = COLORS[mode];
    return color[1], color[2], color[3], true;
end

-- Monotonic-ish Windows clock for smooth movement, independent of frame rate.
-- os.clock is only used as fallback on older Ashita installs.
local function seconds()
    if ashita.time and ashita.time.get_tick then
        return ashita.time.get_tick() * 0.001;
    end
    return os.clock();
end

-- ==========================================================================
-- HideParty dependency and native visibility interlock
-- ==========================================================================
-- This is deliberately two-factor. Checking hidden bytes alone is insufficient:
-- another addon, a stale pointer, or unloading HideParty could leave them at 0.
-- Likewise, checking only AddonManager:IsLoaded() is insufficient because the
-- player can execute /hideparty show. Both conditions must be satisfied.
--
-- Stock HideParty discovers two global locations using this signature and
-- dereferences them to obtain the primitive state. The signature and offsets
-- are compatibility facts documented by GPL-licensed Ashita HideParty; its
-- executable code is NOT copied or bundled in this repository.
local PARTY_TARGET_SIGNATURE = '66C78182000000????C7818C000000????????C781900000';

local function is_32bit_address(value)
    return type(value) == 'number' and value > 0x10000 and value < 0xFFF00000;
end

-- Calling the *real* Ashita 4 addon manager handles missing/unloaded HideParty.
-- Never mistake a folder on disk for proof the addon is running in this session.
local function hideparty_loaded()
    if AddonManager == nil then
        guard.reason = 'Ashita AddonManager is unavailable';
        return false;
    end
    if AddonManager:IsLoaded('hideparty') ~= true then
        guard.reason = 'HideParty is not loaded';
        return false;
    end
    return true;
end

local function find_native_primitives()
    if guard.party_ptr ~= nil and guard.target_ptr ~= nil then
        return true;
    end
    if guard.frame < guard.next_lookup then
        guard.reason = 'waiting to retry native UI discovery';
        return false;
    end
    -- A signature scan is more expensive than two byte reads. Limit retries
    -- on failure; after success the actual visibility is sampled every frame.
    guard.next_lookup = guard.frame + 120;
    local match = ashita.memory.find(0, 0, PARTY_TARGET_SIGNATURE, 0, 0);
    if not is_32bit_address(match) then
        guard.reason = 'HideParty native UI signature not found';
        return false;
    end
    local party = ashita.memory.read_uint32(match + 0x19);
    local target = ashita.memory.read_uint32(match + 0x23);
    if not is_32bit_address(party) or not is_32bit_address(target) then
        guard.reason = 'HideParty native UI pointers not ready';
        return false;
    end
    guard.party_ptr, guard.target_ptr = party, target;
    return true;
end

-- Visibility offsets 0x69 and 0x6A belong to the native primitive object.
-- Stock HideParty writes 0 to BOTH when hidden, and 1 to BOTH when shown.
-- Reject mixed/unknown flags rather than risking a double cursor.
local function both_visibility_flags_hidden(global_pointer_address)
    local holder = ashita.memory.read_uint32(global_pointer_address);
    if not is_32bit_address(holder) then return false; end
    local primitive = ashita.memory.read_uint32(holder + 0x08);
    if not is_32bit_address(primitive) then return false; end
    return ashita.memory.read_uint8(primitive + 0x69) == 0
       and ashita.memory.read_uint8(primitive + 0x6A) == 0;
end

local function can_show_replacement()
    guard.frame = guard.frame + 1;
    guard.allowed = false;

    -- Safe reads during zoning/UI reconstruction. Errors never enable drawing.
    local ok, allowed = pcall(function()
        if not hideparty_loaded() then return false; end
        if not find_native_primitives() then return false; end
        if not both_visibility_flags_hidden(guard.party_ptr) then
            guard.reason = 'native party frame is visible or not ready';
            return false;
        end
        if not both_visibility_flags_hidden(guard.target_ptr) then
            guard.reason = 'native target frame/cursor is visible or not ready';
            return false;
        end
        guard.reason = 'HideParty loaded; native party and target frames hidden';
        return true;
    end);
    if not ok then
        guard.party_ptr, guard.target_ptr = nil, nil;
        guard.reason = 'HideParty state could not be read safely';
        return false;
    end
    guard.allowed = allowed == true;
    return guard.allowed;
end

-- ===========================================================================
-- Native map occlusion
-- ===========================================================================
-- A Direct3D sprite drawn in d3d_present cannot reliably sit behind FFXI's
-- own UI windows. Read FFXI's active menu (Ashita 4's official 'menu' pointer)
-- instead of tracking /map commands or keystrokes, which would miss maps opened
-- from menus and maps dismissed with Escape.
--
-- This read does not alter game memory. If the menu pointer is unavailable,
-- leave the existing target cursor behavior intact, and report that state in
-- /ta status instead of hiding ALL cursors indefinitely.
local map_ui = { open = false, menu = 'unknown' };

local function map_is_open()
    local ok, menu = pcall(function()
        local pm = AshitaCore:GetPointerManager();
        if pm == nil then return nil; end
        local address = pm:Get('menu');
        if not is_32bit_address(address) then return nil; end
        address = ashita.memory.read_uint32(address);
        if not is_32bit_address(address) then return nil; end
        address = ashita.memory.read_uint32(address);
        if not is_32bit_address(address) then return nil; end
        address = ashita.memory.read_uint32(address + 0x04);
        if not is_32bit_address(address) then return nil; end
        return ashita.memory.read_string(address + 0x46, 16);
    end);
    if not ok or type(menu) ~= 'string' then
        map_ui.open = false;
        map_ui.menu = 'unavailable';
        return false;
    end
    -- FFXI menu names are fixed-size strings, frequently null padded. Ashita
    -- reports the native map menu as 'map' (possibly with a menu prefix).
    menu = menu:gsub('%z.*', ''):lower();
    map_ui.menu = menu;
    map_ui.open = menu:find('map', 1, true) ~= nil;
    return map_ui.open;
end

-- ==========================================================================
-- Target acquisition and placement
-- ==========================================================================
-- Preserve the confirmed-working TargetArrow 1.0.1 placement strategy:
-- skeleton generator bone #2 is the model's nameplate attachment position.
-- Crucially, we READ THE MODEL BONE rather than a displayed nameplate. Hiding
-- the nameplate texture does not change the model's underlying bone location.
--
-- The coordinate calculation is intentionally independent of native
-- GetArrowPosition* values. Those were introduced in a later implementation
-- and could yield a marker down by the model's hitbox instead of its head.
--
-- Direct access to actor/skeleton offsets depends on the FFXI client build.
-- Every pointer dereference is defensive and covered by pcall. When a model
-- has no usable skeleton (a door, for example), use a height fallback.

local function acquire_target()
    local mm = AshitaCore:GetMemoryManager();
    if mm == nil then return nil; end
    local target = mm:GetTarget();
    if target == nil then return nil; end
    local slot = target:GetIsSubTargetActive() ~= 0 and 1 or 0;
    draw.target_slot = slot;
    -- Correct Ashita 4 method: GetIsActive (GetActive does not exist).
    if target:GetIsActive(slot) == 0 then return nil; end
    local index = target:GetTargetIndex(slot);
    if type(index) ~= 'number' or index < 1 or index >= 2304 then return nil; end
    return mm:GetEntity(), index, slot;
end

-- Sanity bounds reduce accidental reads from null/stale pointers during
-- zoning. They do not validate virtual-memory page access, so pcall handles
-- exceptions from an inaccessible address.
local function pointer_ok(value)
    return type(value) == 'number' and value > 0x10000 and value < 0xFFF00000;
end

local function coordinate_ok(value)
    return type(value) == 'number' and value == value and math.abs(value) < 50000;
end

-- Read bone #2 from the actor's skeleton generator list. This function is a
-- implementation of the numeric client bone-generator memory layout; it does
-- not depend on a nameplate visibility flag or on HideParty itself.
-- The actor stores X at +0x678, Z at +0x67C, Y at +0x680. The generator
-- stores X at +0x0E, Z at +0x12 and Y at +0x16, and each record is 0x1A.
local function bone_anchor(actor)
    if not pointer_ok(actor) then return nil; end
    local success, x, y, z = pcall(function()
        local skeleton_root = ashita.memory.read_uint32(actor + 0x6B8);
        if not pointer_ok(skeleton_root) then return nil; end
        local skeleton_link = ashita.memory.read_uint32(skeleton_root + 0x0C);
        if not pointer_ok(skeleton_link) then return nil; end
        local skeleton = ashita.memory.read_uint32(skeleton_link);
        if not pointer_ok(skeleton) then return nil; end
        local count = ashita.memory.read_uint16(skeleton + 0x32);
        if type(count) ~= 'number' or count < 3 or count > 256 then return nil; end
        local generator = skeleton + 0x30 + 4 + 0x1E * count + 4 + 2 * 0x1A + 0x0E;
        return ashita.memory.read_float(actor + 0x678) + ashita.memory.read_float(generator),
               ashita.memory.read_float(actor + 0x680) + ashita.memory.read_float(generator + 0x08),
               ashita.memory.read_float(actor + 0x67C) + ashita.memory.read_float(generator + 0x04);
    end);
    if not success or not coordinate_ok(x) or not coordinate_ok(y) or not coordinate_ok(z) then
        return nil;
    end
    return x, y, z;
end

-- Only fall back to entity coordinates when the model bone is unavailable.
-- If a valid bone lies outside the view frustum, we intentionally do NOT
-- switch to a hitbox origin: doing so can show the arrow beside the model.
local function target_anchor(entities, index)
    local kind = entities:GetType(index);
    if kind ~= 3 then
        local x, y, z = bone_anchor(entities:GetActorPointer(index));
        if x ~= nil then return x, y, z, 'nameplate-bone'; end
    end

    local x, y, z;
    if kind == 0 and entities:GetRenderFlags0(index) == 0 then
        x, y, z = entities:GetLastPositionX(index),
                  entities:GetLastPositionY(index),
                  entities:GetLastPositionZ(index);
    else
        x, y, z = entities:GetLocalPositionX(index),
                  entities:GetLocalPositionY(index),
                  entities:GetLocalPositionZ(index);
    end
    if not coordinate_ok(x) or not coordinate_ok(y) or not coordinate_ok(z) then
        return nil;
    end
    return x, y + (kind == 3 and 0.6 or settings.height), z, 'entity-fallback';
end

-- Convert 3D world coordinates into viewport pixels using standard row-vector
-- view and projection transforms. X/Y/Z returned by Ashita correspond to
-- game-world X/height/depth; Direct3D expects X/depth/height respectively.
-- The arithmetic here is ordinary homogeneous-coordinate matrix math.
local function project_world(world_x, world_y, world_z, view, projection, viewport)
    local dx, dy, dz = world_x, world_z, world_y;
    local vx = dx * view._11 + dy * view._21 + dz * view._31 + view._41;
    local vy = dx * view._12 + dy * view._22 + dz * view._32 + view._42;
    local vz = dx * view._13 + dy * view._23 + dz * view._33 + view._43;
    local vw = dx * view._14 + dy * view._24 + dz * view._34 + view._44;
    local cx = vx * projection._11 + vy * projection._21 + vz * projection._31 + vw * projection._41;
    local cy = vx * projection._12 + vy * projection._22 + vz * projection._32 + vw * projection._42;
    local cz = vx * projection._13 + vy * projection._23 + vz * projection._33 + vw * projection._43;
    local cw = vx * projection._14 + vy * projection._24 + vz * projection._34 + vw * projection._44;
    if cw == nil or cw <= 0.01 then return nil; end
    local nx, ny, nz = cx / cw, cy / cw, cz / cw;
    if nx < -1 or nx > 1 or ny < -1 or ny > 1 or nz < 0 or nz > 1 then return nil; end
    return viewport.X + viewport.Width * (nx + 1) / 2,
           viewport.Y + viewport.Height * (1 - ny) / 2;
end

-- ==========================================================================
-- Sprite resources and rendering
-- ==========================================================================
local function open_png(name)
    local output = ffi.new('IDirect3DTexture8*[1]');
    if d3dx.D3DXCreateTextureFromFileA(device, addon.path .. name, output) ~= d3dx.S_OK
       or output[0] == nil then return nil; end
    return d3d.gc_safe_release(ffi.cast('IDirect3DTexture8*', output[0]));
end

local function ensure_resources()
    if sprite ~= nil and main_texture ~= nil and sub_texture ~= nil and main_neutral ~= nil and sub_neutral ~= nil then return true; end
    if device == nil then
        last_render_error = 'Direct3D8 device unavailable';
        return false;
    end
    local output = ffi.new('ID3DXSprite*[1]');
    if d3dx.D3DXCreateSprite(device, output) ~= d3dx.S_OK or output[0] == nil then
        last_render_error = 'Unable to create D3DX sprite';
        return false;
    end
    sprite = d3d.gc_safe_release(ffi.cast('ID3DXSprite*', output[0]));
    main_texture = open_png('arrow.png');
    sub_texture = open_png('subarrow.png');
    main_neutral = open_png('arrow-neutral.png');
    sub_neutral = open_png('subarrow-neutral.png');
    if main_texture == nil or sub_texture == nil or main_neutral == nil or sub_neutral == nil then
        sprite = nil;
        last_render_error = 'Missing/unreadable arrow assets';
        return false;
    end
    last_render_error = 'none';
    return true;
end

local function draw_frame()
    -- HideParty is the only authority for native frame visibility. Never draw
    -- when HideParty is absent, showing frames, or impossible to verify.
    if not settings.enabled then
        draw.stage = 'disabled by user';
        guard.allowed = false;
        return;
    end
    if not can_show_replacement() then
        draw.stage = 'blocked by HideParty guard';
        return;
    end

    -- FFXI renders its native map before addon sprites, so suppress the
    -- replacement cursor while that menu is active. The ordinary draw path
    -- resumes on the next frame after the map is closed.
    if map_is_open() then
        draw.stage = 'hidden while map is open';
        draw.target_index = 0;
        draw.anchor = 'none';
        draw.candidate_count = 0;
        return;
    end

    draw.stage = 'no active target';
    draw.target_index = 0;
    draw.anchor = 'none';
    draw.candidate_count = 0;
    local entities, index, slot = acquire_target();
    if entities == nil then return; end
    draw.target_index = index;

    -- Preserve the tested bone-first anchor and fallback policy.
    draw.stage = 'no usable target position';
    local wx, wy, wz, anchor_kind = target_anchor(entities, index);
    if wx == nil then return; end
    draw.anchor = anchor_kind;
    draw.candidate_count = 1;

    draw.stage = 'camera matrix unavailable';
    if device == nil then return; end
    local _, view = device:GetTransform(d3dx.D3DTS_VIEW);
    local _, projection = device:GetTransform(d3dx.D3DTS_PROJECTION);
    local _, viewport = device:GetViewport();
    if view == nil or projection == nil or viewport == nil then return; end

    draw.stage = 'target outside viewport';
    local px, py = project_world(wx, wy, wz, view, projection, viewport);
    if px == nil then return; end

    draw.stage = 'sprite/texture unavailable';
    if not ensure_resources() then return; end
    sprite_scale.x, sprite_scale.y = settings.scale, settings.scale;
    screen_pos.x = px - WIDTH * settings.scale * 0.5;
    screen_pos.y = py - HEIGHT * settings.scale - settings.offset;

    -- Both effects are disabled by default and calculated AFTER positioning,
    -- so they cannot alter skeleton bone selection or HideParty safety checks.
    -- Pixel bobbing emulates the gentle up/down native target cursor motion.
    local elapsed = (settings.bob == 1 or settings.flash == 1) and seconds() or 0;
    if settings.bob == 1 then
        screen_pos.y = screen_pos.y - math.sin(elapsed * 2 * math.pi * settings.bob_speed) * settings.bob_distance;
    end
    local alpha = 255;
    if settings.flash == 1 then
        local wave = (1 + math.sin(elapsed * 2 * math.pi * settings.flash_speed)) * 0.5;
        alpha = 255 * (1 - settings.flash_strength * (1 - wave));
    end
    local red, green, blue, tinted = color_for(slot);
    local image;
    if slot == 1 then
        image = tinted and sub_neutral or sub_texture;
    else
        image = tinted and main_neutral or main_texture;
    end
    sprite:Draw(image, source_rect, sprite_scale, nil, 0.0, screen_pos,
                rgb_to_u32(red, green, blue, alpha));
    draw.stage = 'draw submitted';
    draw.successes = draw.successes + 1;
end

-- ==========================================================================
-- ImGui configuration: open using /ta config
-- ==========================================================================
-- ImGui's values are single-element tables. The window is intentionally
-- separate from the rendering path so UI errors cannot break the target arrow.
local function draw_config()
    if not ui.open[1] then return; end
    imgui.SetNextWindowSize({ 430, 520 }, ImGuiCond_FirstUseEver);
    if imgui.Begin('TargetArrow - Settings', ui.open) then
        imgui.Text('TargetArrow 1.0.0  |  by 7h3Cub3');
        imgui.TextWrapped('Restores the target cursor when stock HideParty conceals the original party and target UI.');
        imgui.Separator();

        local enabled = { settings.enabled };
        if imgui.Checkbox('Enable TargetArrow', enabled) then
            settings.enabled = enabled[1]; -- /ta on /ta off remain session-only
        end
        imgui.TextWrapped('HideParty: ' .. guard.reason);
        imgui.Text('Last draw: ' .. draw.stage);
        imgui.Text('Map open: ' .. tostring(map_ui.open));
        imgui.Separator();
        imgui.Text('Cursor placement');
        local function slider(label, key, fmt)
            local v = { settings[key] };
            if imgui.SliderFloat(label, v, bounds[key][1], bounds[key][2], fmt or '%.2f') then
                settings[key] = v[1];
                write_settings();
            end
        end
        slider('Scale', 'scale');
        slider('Vertical offset (pixels)', 'offset', '%.0f');
        slider('Fallback model height', 'height');
        imgui.Separator();
        imgui.Text('Cursor colors');

        local main_color = { settings.target_color };
        if imgui.Combo('Target arrow', main_color, COLOR_LABELS) then
            settings.target_color = main_color[1];
            write_settings();
        end
        local sub_color = { settings.sub_color };
        if imgui.Combo('Subtarget arrow', sub_color, COLOR_LABELS) then
            settings.sub_color = sub_color[1];
            write_settings();
        end
        -- Custom colors use the neutral copy of the exact original silhouette,
        -- and D3D vertex color multiplication; no image replacement is needed.
        local function custom_color(prefix, label)
            local rgba = { settings[prefix .. '_r'], settings[prefix .. '_g'], settings[prefix .. '_b'], 1.0 };
            if imgui.ColorEdit4(label, rgba) then
                settings[prefix .. '_r'] = rgba[1];
                settings[prefix .. '_g'] = rgba[2];
                settings[prefix .. '_b'] = rgba[3];
                write_settings();
            end
        end
        if settings.target_color == 8 then custom_color('target', 'Custom target tint'); end
        if settings.sub_color == 8 then custom_color('sub', 'Custom subtarget tint'); end
        imgui.Separator();
        imgui.Text('Optional animation (both OFF by default)');
        local bob = { settings.bob == 1 };
        if imgui.Checkbox('Bobbing - gentle up and down', bob) then
            settings.bob = bob[1] and 1 or 0;
            write_settings();
        end
        if settings.bob == 1 then
            slider('Bobbing speed (cycles/s)', 'bob_speed');
            slider('Bobbing distance (pixels)', 'bob_distance');
        end
        local flash = { settings.flash == 1 };
        if imgui.Checkbox('Flashing - gentle opacity pulse', flash) then
            settings.flash = flash[1] and 1 or 0;
            write_settings();
        end
        if settings.flash == 1 then
            slider('Flashing speed (cycles/s)', 'flash_speed');
            slider('Flashing strength', 'flash_strength');
        end
        imgui.Separator();
        imgui.TextWrapped('Restore original gold/green cursors, size and position; disable bobbing and flashing.');
        if imgui.Button('Restore Defaults') then
            restore_defaults();
        end
        imgui.SameLine();
        if imgui.Button('Close') then ui.open[1] = false; end
    end
    imgui.End();
end

-- ==========================================================================
-- User commands and event handlers
-- ==========================================================================
ashita.events.register('load', 'load_cb', function()
    read_settings();
    notify('v1.0.0 loaded. Requires HideParty to hide both party and target frames. /ta status');
end);

ashita.events.register('command', 'command_cb', function(e)
    local argv = e.command:args();
    if #argv == 0 or not argv[1]:any('/ta', '/targetarrow') then return; end
    e.blocked = true;
    local command = (argv[2] or 'help'):lower();
    if command == 'config' then
        ui.open[1] = not ui.open[1];
        return;
    elseif command == 'status' then
        notify(('v%s | enabled=%s | drawing_allowed=%s | guard=%s | map_open=%s | menu=%s | last_draw=%s | target=%s | candidates=%d | anchor=%s | draws=%d | bob=%s | flash=%s | last_error=%s')
            :format(addon.version, tostring(settings.enabled), tostring(settings.enabled and guard.allowed and not map_ui.open),
                    guard.reason, tostring(map_ui.open), map_ui.menu, draw.stage,
                    tostring(draw.target_index), draw.candidate_count,
                    draw.anchor, draw.successes, tostring(settings.bob == 1),
                    tostring(settings.flash == 1), last_render_error));
        return;
    elseif command == 'on' or command == 'off' then
        settings.enabled = command == 'on';
    elseif command == 'toggle' then
        settings.enabled = not settings.enabled;
    elseif command == 'bob' or command == 'flash' then
        local value = (argv[3] or ''):lower();
        if value ~= 'on' and value ~= 'off' then
            notify('Use /ta ' .. command .. ' on|off');
            return;
        end
        settings[command] = value == 'on' and 1 or 0;
        write_settings();
    elseif command == 'color' or command == 'subcolor' then
        local value = (argv[3] or ''):lower();
        local choice = nil;
        for i, name in ipairs(COLOR_NAMES) do
            if value == name then choice = i - 1; break; end
        end
        if choice == nil then
            notify('Colors: ' .. table.concat(COLOR_NAMES, ', '));
            return;
        end
        settings[command == 'color' and 'target_color' or 'sub_color'] = choice;
        write_settings();
    elseif bounds[command] ~= nil then
        local number = tonumber(argv[3]);
        local range = bounds[command];
        if number == nil or number < range[1] or number > range[2] then
            notify(('%s must be between %s and %s.'):format(command, range[1], range[2]));
            return;
        end
        settings[command] = number;
        write_settings();
    else
        notify('Use: /ta config|on|off|toggle|status|scale|offset|height|bob|flash|color|subcolor.');
        return;
    end
    notify(('enabled=%s | scale=%.2f | offset=%.1f | height=%.1f'):format(
        tostring(settings.enabled), settings.scale, settings.offset, settings.height));
end);

ashita.events.register('d3d_present', 'present_cb', function()
    -- Rendering exceptions do not modify either native frame. Guard state is
    -- fail-closed, and a single diagnostic prevents the chat log from flooding.
    local ok, reason = pcall(draw_frame);
    if not ok then
        guard.allowed = false;
        guard.reason = 'draw failed';
        draw.stage = 'draw error';
        last_render_error = tostring(reason);
        if not render_error_reported then
            render_error_reported = true;
            notify('Draw error (once): ' .. tostring(reason));
        end
    end
    -- A configuration fault is isolated from the renderer and reported once.
    local ui_ok, ui_err = pcall(draw_config);
    if not ui_ok and not ui.error_reported then
        ui.error_reported = true;
        notify('Config window error (once): ' .. tostring(ui_err));
    end
end);
