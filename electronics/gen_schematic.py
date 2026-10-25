"""Generates the Hydra Nexus capsule controller schematic (KiCad .kicad_sch) from a netlist.
Symbols are copied from the official KiCad symbol libraries; every used pin gets a short wire and a
net label, every unused pin a no-connect flag, and PWR_FLAGs are added to supply nets with no driver.
usage: python gen_schematic.py <kicad symbols dir> <out.kicad_sch>"""
import os, re, sys, uuid

SYMDIR, OUT = sys.argv[1], sys.argv[2]

# ----------------------------------------------------------------------------- tiny s-expression reader
def tokenize(s):
    return re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', s)

def parse(tokens, i=0):
    out = []
    while i < len(tokens):
        t = tokens[i]
        if t == '(':
            sub, i = parse(tokens, i + 1)
            out.append(sub)
        elif t == ')':
            return out, i + 1
        else:
            out.append(t)
            i += 1
    return out, i

def dump(e):
    if isinstance(e, list):
        return '(' + ' '.join(dump(x) for x in e) + ')'
    return e

def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

def unq(s):
    return s[1:-1] if s.startswith('"') else s

_libs = {}
def lib_symbol(lib_id):
    lib, name = lib_id.split(':')
    if lib not in _libs:
        data = open(os.path.join(SYMDIR, lib + '.kicad_sym'), encoding='utf8').read()
        tree, _ = parse(tokenize(data))
        _libs[lib] = {unq(s[1]): s for s in tree[0] if isinstance(s, list) and s and s[0] == 'symbol'}
    syms = _libs[lib]
    s = syms[name]
    ext = [x for x in s if isinstance(x, list) and x[0] == 'extends']
    if ext:
        parent = lib_symbol(lib + ':' + unq(ext[0][1]))
        pname = unq(parent[1]).split(':')[-1]
        merged = [parent[0], q(name)]
        own_props = [x for x in s if isinstance(x, list) and x[0] == 'property']
        own_keys = {unq(p[1]) for p in own_props}
        for x in parent[2:]:
            if isinstance(x, list) and x[0] == 'property' and unq(x[1]) in own_keys:
                continue
            if isinstance(x, list) and x[0] == 'symbol':
                x = [x[0], q(unq(x[1]).replace(pname + '_', name + '_', 1))] + x[2:]
            merged.append(x)
        merged[2:2] = own_props
        return merged
    return s

def pins_of(sym):
    """returns {unit: [(number, name, x, y, angle, type, hidden)]}; unit 0 = all units"""
    out = {}
    for sub in sym:
        if isinstance(sub, list) and sub and sub[0] == 'symbol':
            m = re.match(r'.*_(\d+)_(\d+)$', unq(sub[1]))
            unit = int(m.group(1))
            for p in sub:
                if isinstance(p, list) and p and p[0] == 'pin':
                    ptype = p[1]
                    at = [x for x in p if isinstance(x, list) and x[0] == 'at'][0]
                    num = [x for x in p if isinstance(x, list) and x[0] == 'number'][0]
                    nm = [x for x in p if isinstance(x, list) and x[0] == 'name'][0]
                    hidden = 'hide' in p or any(isinstance(x, list) and x[0] == 'hide' and (len(x) < 2 or x[1] == 'yes') for x in p)
                    out.setdefault(unit, []).append((unq(num[1]), unq(nm[1]), float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0, ptype, hidden))
    return out

def nunits(sym):
    us = set(pins_of(sym).keys()) - {0}
    return max(us) if us else 1

# ----------------------------------------------------------------------------- design (netlist)
# (ref, lib_id, value, {pin number: net}, block); pins absent from the map get a no-connect flag
P = []
def part(ref, lib_id, value, nets, block):
    P.append((ref, lib_id, value, nets, block))

GND = 'GND'
# -- power: USB-C input, charger, battery, regulators
part('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C (charge + data)',
     {'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS', 'A1': GND, 'A12': GND, 'B1': GND, 'B12': GND, 'S1': GND,
      'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DN', 'B7': 'USB_DN'}, 'power')
part('R1', 'Device:R', '5.1k', {'1': 'CC1', '2': GND}, 'power')
part('R2', 'Device:R', '5.1k', {'1': 'CC2', '2': GND}, 'power')
part('F1', 'Device:Polyfuse', '500 mA', {'1': 'VBUS', '2': 'VBUS_F'}, 'power')
part('U4', 'Battery_Management:MCP73831-2-OT', 'MCP73831 Li-ion charger', {'4': 'VBUS_F', '3': 'VBAT', '2': GND, '5': 'PROG', '1': 'CHG_STAT'}, 'power')
part('R3', 'Device:R', '2k (500 mA)', {'1': 'PROG', '2': GND}, 'power')
part('R4', 'Device:R', '1k', {'1': 'VBUS_F', '2': 'CHG_LED'}, 'power')
part('D1', 'Device:LED', 'CHARGE', {'2': 'CHG_LED', '1': 'CHG_STAT'}, 'power')
part('C1', 'Device:C', '4.7uF', {'1': 'VBUS_F', '2': GND}, 'power')
part('C2', 'Device:C', '4.7uF', {'1': 'VBAT', '2': GND}, 'power')
part('BT1', 'Device:Battery_Cell', '18650 protected Li-ion', {'1': 'VBAT', '2': GND}, 'power')
part('U5', 'Regulator_Linear:AP2112K-3.3', 'AP2112K-3.3 LDO', {'1': 'VBAT', '3': 'VBAT', '2': GND, '5': '+3V3'}, 'power')
part('C3', 'Device:C', '1uF', {'1': 'VBAT', '2': GND}, 'power')
part('C4', 'Device:C', '1uF', {'1': '+3V3', '2': GND}, 'power')
part('U6', 'Regulator_Switching:MT3608', 'MT3608 boost 5 V', {'5': 'VBAT', '4': 'VBAT', '1': 'SW', '2': GND, '3': 'FB'}, 'power')
part('L1', 'Device:L', '22uH', {'1': 'VBAT', '2': 'SW'}, 'power')
part('D2', 'Device:D_Schottky', 'SS34', {'2': 'SW', '1': '+5V'}, 'power')
part('R5', 'Device:R', '16k', {'1': '+5V', '2': 'FB'}, 'power')
part('R6', 'Device:R', '2.2k', {'1': 'FB', '2': GND}, 'power')
part('C5', 'Device:C', '22uF', {'1': '+5V', '2': GND}, 'power')
part('R33', 'Device:R', '100k', {'1': 'VBAT', '2': 'VBAT_SENSE'}, 'power')
part('R34', 'Device:R', '100k', {'1': 'VBAT_SENSE', '2': GND}, 'power')
part('C11', 'Device:C', '100nF', {'1': 'VBAT_SENSE', '2': GND}, 'power')
# -- controller
part('U1', 'RF_Module:ESP32-C3-WROOM-02', 'ESP32-C3 module',
     {'1': '+3V3', '2': 'EN', '9': GND, '19': GND, '18': 'IR_LED', '17': 'UV_EN', '16': 'MOIST', '15': 'EC_PWR', '3': 'V1_EN', '4': 'V2_EN',
      '5': 'SDA', '6': 'SCL', '7': 'LOCK', '8': 'BTN', '10': 'PUMP_PWM', '13': 'USB_DN', '14': 'USB_DP', '11': 'RGB_DIN', '12': 'ONEWIRE'}, 'mcu')
part('R7', 'Device:R', '10k', {'1': '+3V3', '2': 'EN'}, 'mcu')
part('C6', 'Device:C', '1uF', {'1': 'EN', '2': GND}, 'mcu')
part('C7', 'Device:C', '10uF', {'1': '+3V3', '2': GND}, 'mcu')
part('C8', 'Device:C', '100nF', {'1': '+3V3', '2': GND}, 'mcu')
part('R8', 'Device:R', '4.7k', {'1': '+3V3', '2': 'SDA'}, 'mcu')
part('R9', 'Device:R', '4.7k', {'1': '+3V3', '2': 'SCL'}, 'mcu')
part('SW1', 'Switch:SW_Push', 'USER / WAKE', {'1': 'BTN', '2': GND}, 'mcu')
part('R10', 'Device:R', '10k', {'1': '+3V3', '2': 'BTN'}, 'mcu')
part('R11', 'Device:R', '10k', {'1': '+3V3', '2': 'LOCK'}, 'mcu')
part('J9', 'Connector_Generic:Conn_01x02', 'CAP-LOCK SWITCH', {'1': 'LOCK', '2': GND}, 'mcu')
part('R12', 'Device:R', '100k', {'1': '+3V3', '2': 'MOIST'}, 'mcu')
part('J8', 'Connector_Generic:Conn_01x02', 'MOISTURE TRACES', {'1': 'MOIST', '2': GND}, 'mcu')
part('J6', 'Connector_Generic:Conn_01x04', 'OLED 0.91in I2C', {'1': GND, '2': '+3V3', '3': 'SCL', '4': 'SDA'}, 'mcu')
part('J7', 'Connector_Generic:Conn_01x03', 'RGB RING', {'1': '+5V', '2': 'RGB', '3': GND}, 'mcu')
part('R13', 'Device:R', '330', {'1': 'RGB_DIN', '2': 'RGB'}, 'mcu')
# -- sensing
part('U2', 'Analog_ADC:ADS1115IDGS', 'ADS1115 16-bit ADC', {'8': '+3V3', '3': GND, '1': GND, '9': 'SDA', '10': 'SCL', '4': 'PH_OUT', '5': 'EC_OUT', '6': 'TURB_OUT', '7': 'VBAT_SENSE'}, 'sense')
part('C9', 'Device:C', '100nF', {'1': '+3V3', '2': GND}, 'sense')
part('J3', 'Connector_Generic:Conn_01x03', 'pH via DFR0504 isolator', {'1': 'PH_OUT', '2': '+5V', '3': GND}, 'sense')
part('J4', 'Connector_Generic:Conn_01x03', 'EC/TDS SEN0244 board', {'1': 'EC_OUT', '2': 'EC_PWR', '3': GND}, 'sense')
part('J5', 'Connector_Generic:Conn_01x03', 'DS18B20 probe', {'1': '+3V3', '2': 'ONEWIRE', '3': GND}, 'sense')
part('R14', 'Device:R', '4.7k', {'1': '+3V3', '2': 'ONEWIRE'}, 'sense')
part('U8', 'Amplifier_Operational:MCP6001-OT', 'MCP6001 TIA', {'4': 'TIA_IN', '3': GND, '1': 'TURB_OUT', '5': '+3V3', '2': GND}, 'sense')
part('D3', 'Device:D_Photo', 'IR photodiode (90 deg)', {'1': 'TIA_IN', '2': GND}, 'sense')
part('R15', 'Device:R', '1M', {'1': 'TIA_IN', '2': 'TURB_OUT'}, 'sense')
part('C10', 'Device:C', '10pF', {'1': 'TIA_IN', '2': 'TURB_OUT'}, 'sense')
part('U3', 'Sensor_Energy:INA219AxD', 'INA219 load current', {'8': '+5V', '7': '+5V_LOAD', '5': '+3V3', '6': GND, '3': 'SDA', '4': 'SCL', '1': GND, '2': GND}, 'sense')
part('R16', 'Device:R', '0.1R shunt', {'1': '+5V', '2': '+5V_LOAD'}, 'sense')
# -- low-side drivers and loads
for i, (qref, sig, load, jref, label, fly) in enumerate((
        ('Q1', 'PUMP_PWM', 'PUMP_N', 'J10', 'PUMP P1', True), ('Q2', 'V1_EN', 'V1_N', 'J11', 'VALVE V1', True),
        ('Q3', 'V2_EN', 'V2_N', 'J12', 'VALVE V2', True), ('Q4', 'UV_EN', 'UV_N', 'J13', 'UV-C DRIVER', False), ('Q5', 'IR_LED', 'IR_N', None, None, False))):
    n = 17 + 3 * i
    part(qref, 'Transistor_FET:AO3400A', 'AO3400A', {'1': qref + '_G', '2': GND, '3': load}, 'drive')
    part('R%d' % n, 'Device:R', '100', {'1': sig, '2': qref + '_G'}, 'drive')
    part('R%d' % (n + 1), 'Device:R', '100k', {'1': qref + '_G', '2': GND}, 'drive')
    if jref:
        part(jref, 'Connector_Generic:Conn_01x02', label, {'1': '+5V_LOAD', '2': load}, 'drive')
    if fly:
        part('D%d' % (4 + i), 'Device:D_Schottky', '1N5819', {'1': '+5V_LOAD', '2': load}, 'drive')
part('D9', 'Device:LED', 'IR LED (~860 nm)', {'2': 'IR_A', '1': 'IR_N'}, 'drive')
part('R32', 'Device:R', '150', {'1': '+5V', '2': 'IR_A'}, 'drive')

# ----------------------------------------------------------------------------- layout + emit
U = lambda: str(uuid.uuid4())
ROOT = U()
G = 2.54
def snap(v):
    return round(v / 1.27) * 1.27

items = []
libs_used = {}
net_pins = {}  # net -> list of pin types
placed = []
blocks = {'power': (20, 25), 'mcu': (20, 210), 'sense': (300, 25), 'drive': (300, 210)}
cursor = {k: [v[0], v[1], 0.0] for k, v in blocks.items()}
COLW = {'power': 280, 'mcu': 280, 'sense': 280, 'drive': 280}

def bbox(pins):
    xs = [p[2] for p in pins] or [0]; ys = [p[3] for p in pins] or [0]
    return min(xs), max(xs), min(ys), max(ys)

for ref, lib_id, value, nets, block in P:
    sym = lib_symbol(lib_id)
    libs_used[lib_id] = sym
    pins = pins_of(sym)
    units = nunits(sym)
    for unit in range(1, units + 1):
        up = pins.get(0, []) + pins.get(unit, [])
        x0, x1, y0, y1 = bbox(up)
        lab_len = max([len(nets.get(p[0], '')) for p in up] + [3]) * 1.3 + 8
        w = (x1 - x0) + 2 * lab_len + 10; h = (y1 - y0) + 14
        cx, cy, rowh = cursor[block]
        if cx + w > blocks[block][0] + COLW[block]:
            cx = blocks[block][0]; cy += rowh + 6; rowh = 0
        sx = snap(cx + lab_len + 5 - x0); sy = snap(cy + 7 + y1)
        cursor[block] = [cx + w, cy, max(rowh, h)]
        props = [('Reference', ref, sx, sy - y1 - 3.5), ('Value', value, sx, sy - y0 + 3.5), ('Footprint', '', sx, sy), ('Datasheet', '', sx, sy)]
        prop_s = ' '.join('(property %s %s (at %.2f %.2f 0) (effects (font (size 1.27 1.27))%s))' % (q(k), q(v), px, py, ' (hide yes)' if k in ('Footprint', 'Datasheet') else '')
                          for k, v, px, py in props)
        pin_s = ' '.join('(pin %s (uuid %s))' % (q(p[0]), U()) for p in up)
        items.append('(symbol (lib_id %s) (at %.2f %.2f 0) (unit %d) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid %s) %s %s '
                     '(instances (project "HydraNexus_Capsule" (path "/%s" (reference %s) (unit %d)))))'
                     % (q(lib_id), sx, sy, unit, U(), prop_s, pin_s, ROOT, q(ref), unit))
        for num, nm, px, py, ang, ptype, hidden in up:
            ax, ay = sx + px, sy - py
            net = nets.get(num)
            if hidden and net is None:
                continue
            if net is None:
                items.append('(no_connect (at %.2f %.2f) (uuid %s))' % (ax, ay, U()))
                continue
            net_pins.setdefault(net, []).append(ptype)
            a = int(round(ang)) % 360
            d = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[a]
            ex, ey = ax + d[0] * 2 * G, ay + d[1] * 2 * G
            items.append('(wire (pts (xy %.2f %.2f) (xy %.2f %.2f)) (stroke (width 0) (type default)) (uuid %s))' % (ax, ay, ex, ey, U()))
            lang = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}[d]
            just = 'left bottom' if lang in (0, 90) else 'right bottom'
            items.append('(label %s (at %.2f %.2f %d) (effects (font (size 1.27 1.27)) (justify %s)) (uuid %s))' % (q(net), ex, ey, lang, just, U()))

# PWR_FLAG on supply nets that have power inputs but no power output driving them
flag = lib_symbol('power:PWR_FLAG'); libs_used['power:PWR_FLAG'] = flag
fx, fy = snap(545), snap(30)
for net, types in sorted(net_pins.items()):
    if 'power_in' in types and 'power_out' not in types:
        items.append('(symbol (lib_id "power:PWR_FLAG") (at %.2f %.2f 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid %s) '
                     '(property "Reference" "#FLG%02d" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                     '(property "Value" "PWR_FLAG" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)))) (pin "1" (uuid %s)) '
                     '(instances (project "HydraNexus_Capsule" (path "/%s" (reference "#FLG%02d") (unit 1)))))'
                     % (fx, fy, U(), len(items) % 97, fx, fy - 5, fx, fy - 3.5, U(), ROOT, len(items) % 97))
        items.append('(wire (pts (xy %.2f %.2f) (xy %.2f %.2f)) (stroke (width 0) (type default)) (uuid %s))' % (fx, fy, fx, fy + 2 * G, U()))
        items.append('(label %s (at %.2f %.2f 270) (effects (font (size 1.27 1.27)) (justify right bottom)) (uuid %s))' % (q(net), fx, fy + 2 * G, U()))
        fx += 25.4

def lib_entry(lib_id, sym):
    s = list(sym); s[1] = q(lib_id)
    return dump(s)

title = ('(title_block (title "Hydra Nexus capsule v1 - controller, sensing and drivers") (date "2026-10-25") (rev "0.1") '
         '(comment 1 "Concept schematic generated from the Stage 2 design netlist; AI-assisted, team review pending") '
         '(comment 2 "Symbols: official KiCad libraries. Footprints not yet assigned (PCB is a later step)"))')
texts = ['(text %s (at %.2f %.2f 0) (effects (font (size 3 3) (thickness 0.6) bold) (justify left bottom)) (uuid %s))' % (q(t), x, y, U())
         for t, x, y in (('POWER: USB-C, CHARGER, 18650, 3V3 LDO, 5V BOOST, BATTERY SENSE', 20, 18), ('CONTROLLER & USER I/O', 20, 203),
                         ('SENSING: ADC, pH / EC / TEMP CONNECTORS, TURBIDITY TIA, LOAD CURRENT', 300, 18), ('LOW-SIDE DRIVERS & LOADS', 300, 203),
                         ('PWR_FLAGS', 545, 18))]
doc = ('(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0") (uuid %s) (paper "A2") %s (lib_symbols %s) %s %s '
       '(sheet_instances (path "/" (page "1"))))') % (ROOT, title, ' '.join(lib_entry(k, v) for k, v in libs_used.items()), ' '.join(texts), ' '.join(items))
open(OUT, 'w', encoding='utf8').write(doc)
print('parts', len(P), 'nets', len(net_pins), 'flags', sum(1 for n, t in net_pins.items() if 'power_in' in t and 'power_out' not in t))
