"""Write config/game.toml from xbe_symbols' 4831-signature run plus the OOVPA scans.

    python -I make_config.py trial_4831.toml oovpa.tsv oovpa2.tsv > game.toml

Each address says where it came from. Overrides by hand are in HAND below.
"""
import re
import sys
import tomllib

# name: (value, why) decided by reading the code, applied last
HAND = {
    'D3DDevice_SetRenderStateNotInline': (0x200C00, 'by hand: reads the state, below 0x52 the simple encode '
                                                    'table 0x2656D0, stores D3D_RenderState[state]'),
    'D3DDevice_SetTextureStageStateNotInline': (0x201510, 'by hand: (stage, type, value), ret 0xC, stores '
                                                          '[(stage * 32 + type) * 4 + 0x20FC30]; the D3D code at '
                                                          '0x20209B calls it with stage 1, type 0xC'),
    'IDirectSound_SetMixBinHeadroom': (0x214163, 'by hand: IDirectSound wrapper (this - 8, ret 0xC) of 0x213194, '
                                                 'which stores the headroom byte for mixbin a[1] and tells the DSP; '
                                                 'the game calls it through the thunk 0x4F7F0'),
    'IDirectSoundBuffer_SetRolloffCurve': (0, 'xbe_symbols matched the wrapper 0x2153FB by its bytes; it calls '
                                              'CDirectSoundBuffer_SetConeAngles 0x214C4D (oovpa), so it is '
                                              'IDirectSoundBuffer_SetConeAngles'),
    'IDirectSoundBuffer_AddRef': (0x213003, 'oovpa 3911 (IDirectSoundBuffer_AddRef); by hand: this - 0x1C, calls '
                                            'the object\'s vtable slot 1; the game calls it at 0xDE3A7'),
    'IDirectSound_SetAllParameters': (0x215C8F, 'oovpa 3911; by hand: IDirectSound wrapper (this - 8, ret 0xC) of '
                                                'CDirectSound_SetAllParameters 0x215776, which copies the '
                                                'DS3DLISTENER from +4; the game calls it at 0x19C37B'),
    'CDirectSoundStream_SetOutputBuffer': (0x214FCC, 'oovpa 4134; IDirectSoundStream_SetOutputBuffer 0x215570 jumps '
                                                     'to it; the game calls that at 0x19B7DA'),
    'D3DDevice_Reset': (0x202C70, 'by hand: (pp), ret 4: D3D_KickOffAndWaitForIdle, waits out a pending flip, '
                                  'CDevice_InitializeFrameBuffers(pp), SetRenderTarget(back buffer, auto depth), '
                                  'Clear; the game calls it at 0x162E7B'),
    'D3D_InitDefaultState': (0x208D30, 'by hand: no arguments; identity transforms, render states 57 to 145 from '
                                       'the table 0x20EC90 through SetRenderStateNotInline, texture stage defaults, '
                                       'SetScreenSpaceOffset(0, 0); the device init 0x2098E6 calls it'),
    'IDirectSoundBuffer_SetPitch': (0x2141B6, 'oovpa 4039; wrapper (this - 0x1C, ret 8) of '
                                              'CDirectSoundBuffer_SetPitch 0x213CD8; the DSOUND code at 0x21F964 '
                                              'calls it on a host buffer'),
    'CDirectSoundStream_SetPitch': (0x213EAC, 'oovpa 4134; IDirectSoundStream_SetPitch 0x21438B jumps to it'),
    'IDirectSoundBuffer_SetLFO': (0x2141D2, 'oovpa 4039; wrapper (this - 0x1C, ret 8); the DSOUND synth 0x21F989 calls it'),
    'IDirectSoundBuffer_SetNotificationPositions': (0x214366, 'oovpa 3911; wrapper (ret 0xC); the DSOUND synth 0x21FB2A calls it'),
    'IDirectSoundBuffer_SetConeAngles': (0x2153FB, 'by hand: the wrapper xbe_symbols took for SetRolloffCurve; it calls '
                                                   'CDirectSoundBuffer_SetConeAngles 0x214C4D (ret 0x10)'),
    'IDirectSoundBuffer_SetConeOrientation': (0x21541F, 'oovpa 3911; wrapper (ret 0x14)'),
    'IDirectSoundBuffer_SetConeOutsideVolume': (0x215454, 'oovpa 4039; wrapper (ret 0xC)'),
    'IDirectSoundBuffer_SetMode': (0x2154BC, 'by hand: wrapper (this - 0x1C, ret 0xC) between SetMinDistance 0x215498 '
                                             'and SetPosition 0x2154DC, the interface order'),
    'CDirectSoundStream_SetLFO': (0x213F50, 'oovpa 4134; IDirectSoundStream_SetLFO 0x214390 jumps to it'),
    'CDirectSoundStream_SetEG': (0x213FA2, 'oovpa 4134; IDirectSoundStream_SetEG 0x214395 jumps to it'),
    'CDirectSoundStream_SetAllParameters': (0x21501E, 'oovpa 4134; IDirectSoundStream_SetAllParameters 0x215575 jumps to it'),
    'CDirectSoundStream_SetConeAngles': (0x215074, 'oovpa 4134; IDirectSoundStream_SetConeAngles 0x21557A jumps to it'),
    'CDirectSoundStream_SetConeOrientation': (0x2150CE, 'oovpa 4134 (ret 0x14)'),
    'CDirectSoundStream_SetConeOutsideVolume': (0x215139, 'oovpa 4134 (ret 0xC)'),
    'IDirectSound_CreateSoundStream': (0x215F2E, 'by hand: wrapper (this - 8, ret 0x10) of '
                                                 'CDirectSound_CreateSoundStream 0x215CEF; the DSOUND synth 0x21FC0D '
                                                 'calls it'),
    'CDirectSoundStream_SetMaxDistance': (0x21518F, 'by hand: IDirectSoundStream_SetMaxDistance 0x2155AD calls it '
                                                    '(ret 0xC), it calls CDirectSoundVoice_SetMaxDistance 0x2148EB'),
    'CDirectSoundStream_SetMinDistance': (0x2151E9, 'by hand: IDirectSoundStream_SetMinDistance 0x2155C5 calls it '
                                                    '(ret 0xC), it calls 0x21491E as the buffer\'s SetMinDistance does'),
    'CDirectSoundStream_SetMode': (0x215243, 'by hand: IDirectSoundStream_SetMode 0x2155DD jumps to it (ret 0xC), it '
                                             'calls 0x214951 as the buffer\'s SetMode does'),
    'CDirectSoundStream_SetMixBinVolumes': (0x2140EA, 'by hand: IDirectSoundStream_SetMixBinVolumes 0x2143A9 jumps to '
                                                      'it (ret 8), it calls 0x2133BE as the buffer\'s does'),
    'DirectSoundGetSampleTime': (0x21302F, 'oovpa 3911; by hand: reads the APU sample counter 0xFE80200C when the '
                                           'library\'s DirectSound exists; DirectMusic\'s reference clock 0xEC8A5 '
                                           'calls it at 0xEC8CD'),
    'XInputGetCapabilities': (0, 'xbe_symbols matched 0x25DB04 by constants (0.60); that code claims a '
                                 'device slot and counts opens, XInputOpen\'s job (XInputOpen is 0x25900D)'),
}
DATA_HAND = {
    'D3D_pDevice': (0x212E70, 'Direct3D_CreateDevice 0x205A43 stores D3D_Device in it; D3DDevice_SetTexture '
                              '0x203A7A and the other device calls load it'),
    'D3D_RenderState': (0x20FE30, 'D3DDevice_SetRenderStateNotInline 0x200C1D stores [state * 4 + it]; 19 '
                                  'SetRenderState_* setters store their state there with the 4361 numbering'),
    'D3D_SimpleRenderStateEncode': (0x2656D0, 'D3DDevice_SetRenderStateNotInline 0x200C0A reads [state * 4 + it] '
                                              'for states below 82'),
    'D3D_DeferredTextureState': (0x20FC30, 'D3DDevice_SetTextureStageStateNotInline 0x20153C and 0x20159B store '
                                           '[(stage * 32 + type) * 4 + it]'),
    'D3D_DirtyFlags': (0x20FC28, 'D3DDevice_SetTexture 0x203AF5 ors 0x4800 into it, D3DDevice_SetStreamSource '
                                 '0x204FC0 ors 0x40'),
}


def main():
    trial_path, *tsvs = sys.argv[1:]
    text = open(trial_path, encoding='utf-8').read()
    cfg = tomllib.loads(text)
    sdk = cfg['symbols']
    # per-name comments xbe_symbols wrote ("found by constants", vtable notes) and its log
    comments = {}
    for line in text.splitlines():
        m = re.match(r'(\w+)\s*=\s*\S+\s*#\s*(.*)', line)
        if m:
            comments[m.group(1)] = m.group(2)
    ov = {}
    for path in tsvs:
        for line in open(path):
            n, a, ver, cnt, lib, note = line.rstrip('\n').split('\t')
            ov.setdefault(n, (int(a, 16), ver, lib))

    out = []
    head, rest = text.split('[symbols]', 1)
    head = head.replace('# Recompiler input for default.xbe, written by xbe_symbols',
                        '# Recompiler input for default.xbe. Made from xbe_symbols with the XDK 4831 signatures standing in\n'
                        '# for 4361, then filled from XbSymbolDatabase\'s 4361 patterns (OOVPA, matched as data by a\n'
                        '# script; see docs/HANDOFF.md) and by reading the code. Each address says where it came from:\n'
                        '#   sig       xbe_symbols matched the 4831 signature bytes\n'
                        '#   k=<score> xbe_symbols matched by constants only, checked by eye where noted\n'
                        '#   oovpa <v> an XbSymbolDatabase pattern of revision <v> matched (both agree on all 46 they share)\n'
                        '# Names at 0 are not linked in Hunter or not found yet; the host traps if one it needs is called.')
    # the 4361 overlay instead of [xbe] xdk, and where the header values were proven
    head = head.replace('\n\n[xbe]\n', '\n#\n# The XDK 4361 layouts come from the overlay below: the SDK ships 4831 and 5849 only, and\n'
                                       '# [xbe] xdk = 4361 would look for sdk/xdk/4361/layout.toml.\n'
                                       'includes = ["xdk/4361/layout.toml"]\n\n[xbe]\n', 1)
    head = re.sub(r'(?m)^xdk = \d+\n', '', head)
    head = re.sub(r'(?m)^(title = \S+)$', r'\1  # certificate title id, tools/xbeinfo.py', head)
    head = re.sub(r'(?m)^(entry = \S+)$', r'\1  # header entry XOR the retail key 0xA8FC57AB, tools/xbeinfo.py', head)
    head = re.sub(r'(?m)^code_sections', '# DOLBY is left out: it holds the Dolby Digital encoder\'s DSP image, not x86 '
                                         '(docs/FINDINGS.md)\ncode_sections', head)
    out.append(head + '[symbols]')
    width = max(len(n) for n in sdk)
    kscore = dict(re.findall(r'(\w+) found by constants \(([\d.]+)\)',
                             open('trial.log', encoding='utf-8').read()))
    counts = {'sig': 0, 'k': 0, 'oovpa': 0, 'hand': 0, 'zero': 0}
    for name, val in sdk.items():
        why = ''
        if name in HAND:
            val, why = HAND[name]
            counts['hand'] += 1
        elif val:
            note = comments.get(name, '')
            src = 'sig'
            if name in ov and ov[name][0] != val:
                raise SystemExit(f'{name}: xbe_symbols {val:#x} vs oovpa {ov[name][0]:#x}')
            src = f'k={kscore[name]}' if name in kscore else 'sig'
            why = src + (f', oovpa {ov[name][1]}' if name in ov else '') + (f'; {note}' if note else '')
            if name == 'D3DDevice_SetRenderState_StencilEnable':
                why += '; by eye: loads the device, makes push space, reads the stencil render states'
            if name == 'D3D_MakeRequestedSpace':
                why += '; the oovpa D3DDevice_MakeSpace pattern calls it'
            counts['k' if name in kscore else 'sig'] += 1
        elif name in ov:
            val = ov[name][0]
            why = f'oovpa {ov[name][1]}'
            counts['oovpa'] += 1
        else:
            counts['zero'] += 1
        line = f'{name:<{width}} = {"0x%X" % val if val else "0"}'
        out.append(line + (f'  # {why}' if why else ''))

    # names the SDK's signature set does not list, which the runtime here replaces
    for name, (val, why) in HAND.items():
        if name not in sdk:
            out.append(f'{name:<{width}} = {"0x%X" % val if val else "0"}  # {why}')
            counts['hand'] += 1

    data = cfg.get('data', {})
    out.append('\n[data]')
    dw = max(len(n) for n in data)
    for name, val in data.items():
        why = 'xbe_symbols' if val else ''
        if name in DATA_HAND:
            val, why = DATA_HAND[name]
        out.append(f'{name:<{dw}} = {"0x%X" % val if val else "0"}' + (f'  # {why}' if why else ''))
    out.append('')
    sys.stdout.write('\n'.join(out))
    print(f'# {counts}', file=sys.stderr)


if __name__ == '__main__':
    main()
