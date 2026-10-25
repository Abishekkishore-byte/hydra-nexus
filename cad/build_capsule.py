"""Hydra Nexus capsule v1: parametric FreeCAD (PartDesign) model.
Run with FreeCADCmd:  FreeCADCmd.exe build_capsule.py
Writes HydraNexus_Capsule_v1.FCStd and HydraNexus_Capsule_v1.step next to this script.
All dimensions are driven by the 'Params' spreadsheet (mm). Concept design: dimensions to be confirmed by the team."""
import os
import FreeCAD as App
import Part
import Sketcher
import Spreadsheet  # noqa: F401  (registers Spreadsheet::Sheet)

HERE = os.path.dirname(os.path.abspath(__file__))
V = App.Vector
doc = App.newDocument('HydraNexus_Capsule_v1')

# ------------------------------------------------------------------ parameters
P = doc.addObject('Spreadsheet::Sheet', 'Params')
params = [
    ('ShellOD', 60, 'Shell outer diameter'), ('Wall', 2, 'Shell wall'), ('ShellH', 178, 'Shell height'), ('Base', 6, 'Base thickness'),
    ('CoreX', -10, 'Wet-core axis offset'), ('CartOD', 36, 'Cartridge OD'), ('CartBore', 28, 'Cartridge media bore'), ('CartZ', 72, 'Cartridge base height'),
    ('CartH', 78, 'Cartridge length'), ('CellOD', 34, 'Sensing cell OD'), ('CellID', 28, 'Sensing cell ID'), ('CellZ', 48, 'Cell base height'),
    ('CellH', 22, 'Cell height'), ('UVOD', 24, 'UV-C chamber OD'), ('UVZ', 152, 'UV-C base height'), ('UVH', 16, 'UV-C height'),
    ('SpineX', 16, 'Dry-spine axis offset'), ('CellDia18650', 18.6, '18650 cell diameter'), ('CellLen18650', 65, '18650 cell length'),
    ('SpoutD', 10, 'Spout OD'), ('SpoutH', 12, 'Spout height'),
]
P.set('A1', 'Parameter'); P.set('B1', 'Value (mm)'); P.set('C1', 'Description')
for i, (name, val, desc) in enumerate(params, start=2):
    P.set('A%d' % i, name); P.set('B%d' % i, str(val)); P.set('C%d' % i, desc); P.setAlias('B%d' % i, name)
doc.recompute()

def plane(body, role):
    for f in body.Origin.OriginFeatures:
        if f.Role == role:
            return f
    raise KeyError(role)

def new_body(name, x_expr=None, z=0):
    b = doc.addObject('PartDesign::Body', name)
    if x_expr:
        b.setExpression('.Placement.Base.x', x_expr)
    b.Placement.Base.z = z
    return b

def sketch(body, name, role='XY_Plane', z_expr=None, z=0.0):
    sk = body.newObject('Sketcher::SketchObject', name)
    sk.AttachmentSupport = (plane(body, role), [''])
    sk.MapMode = 'FlatFace'
    sk.AttachmentOffset = App.Placement(V(0, 0, z), App.Rotation())
    if z_expr:
        sk.setExpression('.AttachmentOffset.Base.z', z_expr)
    return sk

def profile(sk, pts, dims=(), lock_origin=True):
    """closed polyline; dims: list of (constraint_type, geo_index, expression)"""
    n = len(pts)
    for i in range(n):
        sk.addGeometry(Part.LineSegment(V(pts[i][0], pts[i][1], 0), V(pts[(i + 1) % n][0], pts[(i + 1) % n][1], 0)), False)
    for i in range(n):
        sk.addConstraint(Sketcher.Constraint('Coincident', i, 2, (i + 1) % n, 1))
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if abs(a[1] - b[1]) < 1e-9:
            sk.addConstraint(Sketcher.Constraint('Horizontal', i))
        elif abs(a[0] - b[0]) < 1e-9:
            sk.addConstraint(Sketcher.Constraint('Vertical', i))
    if lock_origin:
        sk.addConstraint(Sketcher.Constraint('Coincident', 0, 1, -1, 1))  # first point on origin
    else:
        sk.addConstraint(Sketcher.Constraint('PointOnObject', 0, 1, -2))  # first point on the revolve axis
    for kind, gi, expr in dims:
        a, b = pts[gi], pts[(gi + 1) % len(pts)]
        val = abs(b[0] - a[0]) if kind == 'DistanceX' else abs(b[1] - a[1])
        ci = sk.addConstraint(Sketcher.Constraint(kind, gi, 1, gi, 2, val if (b[0] - a[0] if kind == 'DistanceX' else b[1] - a[1]) >= 0 else -val))
        sk.setExpression('Constraints[%d]' % ci, expr)
    return sk

def circle(sk, cx, cy, r, r_expr=None, centre_on_origin=False):
    gi = sk.addGeometry(Part.Circle(V(cx, cy, 0), V(0, 0, 1), r), False)
    ci = sk.addConstraint(Sketcher.Constraint('Diameter', gi, 2 * r))
    if r_expr:
        sk.setExpression('Constraints[%d]' % ci, r_expr)
    if centre_on_origin:
        sk.addConstraint(Sketcher.Constraint('Coincident', gi, 3, -1, 1))
    return gi

def rect(sk, x0, y0, x1, y1):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    base = sk.GeometryCount
    for i in range(4):
        sk.addGeometry(Part.LineSegment(V(pts[i][0], pts[i][1], 0), V(pts[(i + 1) % 4][0], pts[(i + 1) % 4][1], 0)), False)
    for i in range(4):
        sk.addConstraint(Sketcher.Constraint('Coincident', base + i, 2, base + (i + 1) % 4, 1))
    sk.addConstraint(Sketcher.Constraint('Horizontal', base)); sk.addConstraint(Sketcher.Constraint('Horizontal', base + 2))
    sk.addConstraint(Sketcher.Constraint('Vertical', base + 1)); sk.addConstraint(Sketcher.Constraint('Vertical', base + 3))
    sk.addConstraint(Sketcher.Constraint('DistanceX', base, 1, base, 2, x1 - x0))
    sk.addConstraint(Sketcher.Constraint('DistanceY', base + 1, 1, base + 1, 2, y1 - y0))

def pad(body, name, sk, length, expr=None, reversed_=False):
    f = body.newObject('PartDesign::Pad', name)
    f.Profile = sk; f.Length = length; f.Reversed = reversed_
    if expr:
        f.setExpression('Length', expr)
    sk.Visibility = False
    return f

def pocket(body, name, sk, length, expr=None, reversed_=False, midplane=False):
    f = body.newObject('PartDesign::Pocket', name)
    f.Profile = sk; f.Length = length; f.Reversed = reversed_
    if midplane:
        f.Midplane = True
    if expr:
        f.setExpression('Length', expr)
    sk.Visibility = False
    return f

def revolve(body, name, sk):
    f = body.newObject('PartDesign::Revolution', name)
    f.Profile = sk; f.ReferenceAxis = (sk, ['V_Axis']); f.Angle = 360
    sk.Visibility = False
    return f

# ------------------------------------------------------------------ shell (revolved, open top)
shell = new_body('Shell')
sk = sketch(shell, 'ShellProfile', 'XZ_Plane')
profile(sk, [(0, 0), (30, 0), (30, 178), (28, 178), (28, 6), (0, 6)],
        dims=[('DistanceX', 0, 'Params.ShellOD / 2'), ('DistanceY', 1, 'Params.ShellH'), ('DistanceX', 2, '-Params.Wall'), ('DistanceY', 5, '-Params.Base')])
revolve(shell, 'ShellRevolution', sk)
sk = sketch(shell, 'OLEDWindowSketch', 'YZ_Plane', z=29)
rect(sk, -10, 128, 10, 152)
pocket(shell, 'OLEDWindow', sk, 8, midplane=True)
sk = sketch(shell, 'USBCSlotSketch', 'YZ_Plane', z=29)
rect(sk, -4.5, 18, 4.5, 23)
pocket(shell, 'USBCSlot', sk, 8, midplane=True)
sk = sketch(shell, 'ButtonHoleSketch', 'YZ_Plane', z=29)
circle(sk, 0, 113, 3.5)
pocket(shell, 'ButtonHole', sk, 8, midplane=True)
sk = sketch(shell, 'IntakePortSketch', 'XZ_Plane', z=29)
circle(sk, 0, 22, 3)
pocket(shell, 'IntakePort', sk, 8, midplane=True)

# ------------------------------------------------------------------ top cap with spout
cap = new_body('TopCap')
sk = sketch(cap, 'CapProfile', 'XZ_Plane')
profile(sk, [(0, 178), (30, 178), (30, 186), (26, 190), (20, 194), (6, 196), (0, 196)], lock_origin=False)
ci = sk.addConstraint(Sketcher.Constraint('DistanceY', -1, 1, 0, 1, 178))
sk.setExpression('Constraints[%d]' % ci, 'Params.ShellH')
revolve(cap, 'CapRevolution', sk)
sk = sketch(cap, 'SpoutSketch', 'XY_Plane', z=195)
circle(sk, -10, -2, 5, 'Params.SpoutD')
pad(cap, 'Spout', sk, 12, 'Params.SpoutH')
sk = sketch(cap, 'SpoutBoreSketch', 'XY_Plane', z=207)
circle(sk, -10, -2, 3)
pocket(cap, 'SpoutBore', sk, 40)

# ------------------------------------------------------------------ twist-lock cartridge (body placed on the wet-core axis)
cart = new_body('Cartridge', 'Params.CoreX')
sk = sketch(cart, 'CartridgeOutline', 'XY_Plane', 'Params.CartZ', 72)
circle(sk, 0, 0, 18, 'Params.CartOD', True)
pad(cart, 'CartridgeHousing', sk, 78, 'Params.CartH')
sk = sketch(cart, 'MediaBoreSketch', 'XY_Plane', 'Params.CartZ + Params.CartH', 150)
circle(sk, 0, 0, 14, 'Params.CartBore', True)
pocket(cart, 'MediaBore', sk, 74, 'Params.CartH - 4')
sk = sketch(cart, 'BayonetLugSketch', 'XY_Plane', z=140)
rect(sk, 17.5, -3, 21.5, 3)
lug = pad(cart, 'BayonetLug', sk, 4)
pat = cart.newObject('PartDesign::PolarPattern', 'BayonetLugPattern')
pat.Originals = [lug]; pat.Axis = (cart.Origin.OriginFeatures[2], ['']); pat.Angle = 360; pat.Occurrences = 3
for f in cart.Origin.OriginFeatures:
    if f.Role == 'Z_Axis':
        pat.Axis = (f, [''])
cart.Tip = pat

# ------------------------------------------------------------------ shared sensing cell
cell = new_body('SensingCell', 'Params.CoreX')
sk = sketch(cell, 'CellOutline', 'XY_Plane', 'Params.CellZ', 48)
circle(sk, 0, 0, 17, 'Params.CellOD', True)
pad(cell, 'CellBody', sk, 22, 'Params.CellH')
sk = sketch(cell, 'CellCavitySketch', 'XY_Plane', 'Params.CellZ + Params.CellH', 70)
circle(sk, 0, 0, 14, 'Params.CellID', True)
pocket(cell, 'CellCavity', sk, 18, 'Params.CellH - 4')
sk = sketch(cell, 'ProbeGlandSketch', 'XY_Plane', 'Params.CellZ + Params.CellH', 70)
for (px, py, pr) in ((-7, 6, 3.6), (6, 7, 2.0), (7, -6, 2.0), (-6, -7, 3.0)):
    circle(sk, px, py, pr)
pad(cell, 'ProbeGlands', sk, 5)

# ------------------------------------------------------------------ UV-C chamber
uv = new_body('UVC_Chamber', 'Params.CoreX')
sk = sketch(uv, 'UVOutline', 'XY_Plane', 'Params.UVZ', 152)
circle(sk, 0, 0, 12, 'Params.UVOD', True)
pad(uv, 'UVHousing', sk, 16, 'Params.UVH')
sk = sketch(uv, 'QuartzBoreSketch', 'XY_Plane', 'Params.UVZ + Params.UVH', 168)
circle(sk, 0, 0, 8, None, True)
pocket(uv, 'QuartzBore', sk, 12)

# ------------------------------------------------------------------ micro pump + valve block
pump = new_body('MicroPump', 'Params.CoreX')
sk = sketch(pump, 'PumpFootprint', 'XY_Plane', z=8)
rect(sk, -10, -9, 10, 9)
pad(pump, 'PumpBody', sk, 32)
sk = sketch(pump, 'PumpHeadSketch', 'XY_Plane', z=40)
circle(sk, 5, 0, 6)
pad(pump, 'PumpHead', sk, 6)
valves = new_body('ValveBlock', 'Params.CoreX')
sk = sketch(valves, 'ValveFootprint', 'XY_Plane', z=30)
rect(sk, -4, -16, 4, -10)
rect(sk, -4, 10, 4, 16)
pad(valves, 'ValveBodies', sk, 14)

# ------------------------------------------------------------------ dry spine with 18650 bay and PCB slot
spine = new_body('DrySpine', 'Params.SpineX')
sk = sketch(spine, 'SpineFootprint', 'XY_Plane', z=14)
rect(sk, -6, -12, 6, 12)
pad(spine, 'SpineBlock', sk, 150)
sk = sketch(spine, 'BatteryBaySketch', 'XY_Plane', z=14)
circle(sk, 0, 0, 9.5, 'Params.CellDia18650 + 0.4', True)
pocket(spine, 'BatteryBay', sk, 68, 'Params.CellLen18650 + 3', reversed_=True)
sk = sketch(spine, 'PCBSlotSketch', 'XY_Plane', z=164)
rect(sk, -1.2, -12, 1.2, 12)
pocket(spine, 'PCBSlot', sk, 72)

batt = new_body('Cell18650', 'Params.SpineX')
sk = sketch(batt, 'CellCircle', 'XY_Plane', z=15)
circle(sk, 0, 0, 9.3, 'Params.CellDia18650', True)
pad(batt, 'LiIonCell', sk, 65, 'Params.CellLen18650')

doc.recompute()
bad = [o.Name for o in doc.Objects if hasattr(o, 'isValid') and not o.isValid()]
bodies = [o for o in doc.Objects if o.TypeId == 'PartDesign::Body']
for b in bodies:
    print('%-12s valid=%s volume=%.0f mm3' % (b.Name, b.Shape.isValid(), b.Shape.Volume))
print('invalid features:', bad)
doc.saveAs(os.path.join(HERE, 'HydraNexus_Capsule_v1.FCStd'))
import Import
Import.export(bodies, os.path.join(HERE, 'HydraNexus_Capsule_v1.step'))
print('saved')
