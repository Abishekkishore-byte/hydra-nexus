"""Conceptual CAD-style renders of the proposed pocket-size Hydra Nexus capsule (dimensions in mm, concept only).
Outputs: cap_hero.png, cap_assembly.png (numbered + dimensions), cap_exploded.png (numbered)."""
import math, os, sys
from PIL import ImageDraw, ImageFont
import iso
from iso import Canvas, hexc, shade, C30, S30

YMAX = 120

class Cap(Canvas):
    def P(self, x, y, z):
        y = YMAX - y
        X = (x - y) * C30 * self.s + self.ox
        Y = ((x + y) * S30 - z) * self.s + self.oy
        return (X, Y)

    def label(self, at3, dx, dy, txt, size=13):
        d = ImageDraw.Draw(self.img)
        f = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', int(size * iso.SS))
        a = self.P(*at3)
        d.text((a[0] + dx * iso.SS, a[1] + dy * iso.SS), txt, font=f, fill=hexc('0F172A'))

    def dim(self, a3, b3, txt, off=(0, 0)):
        d = ImageDraw.Draw(self.img)
        a = self.P(*a3); b = self.P(*b3); SS = iso.SS
        col = hexc('475569')
        d.line([a, b], fill=col, width=int(1.4 * SS))
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for p, s in ((a, 1), (b, -1)):
            L = 9 * SS
            pts = [p, (p[0] + s * L * math.cos(ang - 0.35), p[1] + s * L * math.sin(ang - 0.35)),
                   (p[0] + s * L * math.cos(ang + 0.35), p[1] + s * L * math.sin(ang + 0.35))]
            d.polygon(pts, fill=col)
        f = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', int(14 * SS))
        m = ((a[0] + b[0]) / 2 + off[0] * SS, (a[1] + b[1]) / 2 + off[1] * SS)
        tw = d.textlength(txt, font=f)
        d.rectangle([m[0] - tw / 2 - 4 * SS, m[1] - 10 * SS, m[0] + tw / 2 + 4 * SS, m[1] + 10 * SS], fill=(255, 255, 255, 235))
        d.text((m[0] - tw / 2, m[1] - 8 * SS), txt, font=f, fill=hexc('0F172A'))

WC = (48, 60)      # wet-core axis
SP = (80, 60)      # dry-spine battery axis

def capsule(cv, E=0.0, markers=False, shell=True, dims=False):
    zc = lambda base, k: base + k * E
    wx, wy = WC
    shx = -95 * E
    if shell:
        cv.cyl(60 + shx, 60, 0, 6, 29, '94A3B8')                                     # base ring (drawn first)
    # ---- dry spine (right side): battery, PCB  (exploded: pulled right)
    sx = 55 * E
    cv.cyl(SP[0] + sx, SP[1], zc(14, -10), zc(80, -10), 9.3, '1D4ED8', bands=((zc(14, -10), zc(20, -10), '0F172A'), (zc(74, -10), zc(80, -10), '94A3B8')))
    cv.box(70 + sx, 48, zc(92, 10), 74 + sx, 72, zc(165, 10), '15803D')            # controller PCB
    cv.box(74 + sx, 52, zc(130, 10), 76 + sx, 64, zc(146, 10), 'CBD5E1')           # ESP32-C3 module can
    cv.box(74 + sx, 54, zc(104, 10), 75.5 + sx, 66, zc(116, 10), '1F2937')         # ADC / driver ICs
    # ---- wet core stack (bottom to top)
    cv.box(wx - 14, wy - 10, zc(8, -40), wx + 10, wy + 10, zc(40, -40), '334155')   # micro diaphragm pump
    cv.cyl(wx + 4, wy, zc(40, -40), zc(46, -40), 7, '64748B')
    cv.box(wx - 16, wy - 15, zc(30, -40), wx - 8, wy - 7, zc(44, -40), '0F172A')    # V1 3-way valve
    # sensing cell (shared)
    cv.cyl(wx, wy, zc(48, -5), zc(70, -5), 17, '3B82F6', alpha=140)
    for (dx, dy, c, r, h) in ((-7, 6, '111827', 3.2, 16), (6, 7, '94A3B8', 1.3, 13), (7, -6, 'F8FAFC', 1.3, 13), (-6, -7, '7F1D1D', 2.4, 9)):
        cv.cyl(wx + dx, wy + dy, zc(52, -5 + 20), zc(52 + h, -5 + 20), r, c)
    # filter cartridge: carbon (lower) + hollow-fibre UF (upper), bayonet band
    cv.cyl(wx, wy, zc(72, 20), zc(150, 20), 18, 'F1F5F9', bands=((zc(72, 20), zc(108, 20), '374151'), (zc(108, 20), zc(113, 20), '0EA5E9'), (zc(146, 20), zc(150, 20), '0EA5E9')))
    if E > 0:
        for k in range(-3, 4):
            cv.dashed((wx + 4 * k, wy - 18, zc(115, 20)), (wx + 4 * k, wy - 18, zc(144, 20)), 'CBD5E1', 1.0, 4)
    # UV-C chamber
    cv.cyl(wx, wy, zc(152, 40), zc(168, 40), 12, 'E9D5FF', alpha=230, bands=((zc(152, 40), zc(155, 40), '7C3AED'), (zc(165, 40), zc(168, 40), '7C3AED')))
    # V2 + top bulkhead
    cv.box(wx - 5, wy - 16, zc(169, 55), wx + 5, wy - 6, zc(178, 55), '0F172A')
    # ---- shell (translucent) with domed top cap
    if shell:
        cv.cyl(60 + shx, 60, 6, 178, 30, 'E2E8F0', alpha=60, edge=hexc('94A3B8'))
        cv.cyl(60 + shx, 60, 70, 125, 30.6, '0F766E', alpha=38, edge=hexc('0F766E'))  # silicone grip sleeve
    # top cap (exploded: lifted)
    tz = 85 * E; tx = 0
    cv.cyl(60, 60, 178 + tz, 184 + tz, 30, '0EA5E9', alpha=220)                     # status LED ring
    for k, r in enumerate((30, 28.5, 26, 22, 16)):
        cv.cyl(60, 60, 184 + tz + k * 3, 187 + tz + k * 3, r, 'CBD5E1')
    cv.cyl(wx, wy - 2, 199 + tz, 210 + tz, 5, '475569', top_col='0F172A')       # outlet spout
    # ---- shell-mounted UI on the right face (x = 90 plane)
    if shell:
        u = shx
        cv.poly([(90.6 + u, 50, 128), (90.6 + u, 70, 128), (90.6 + u, 70, 152), (90.6 + u, 50, 152)], hexc('0F172A'))
        cv.poly([(90.8 + u, 52, 131), (90.8 + u, 68, 131), (90.8 + u, 68, 149), (90.8 + u, 52, 149)], hexc('22D3EE'))
        cv.poly([(90.6 + u, 55, 108), (90.6 + u, 65, 108), (90.6 + u, 65, 118), (90.6 + u, 55, 118)], hexc('0F766E'))   # button
        cv.poly([(90.6 + u, 54, 18), (90.6 + u, 66, 18), (90.6 + u, 66, 23), (90.6 + u, 54, 23)], hexc('111827'))       # USB-C
    # ---- intake hose with weighted pre-mesh, reject port
    if E == 0:
        cv.tube([(30, 40, 22), (5, 30, 18), (-25, 20, 6), (-45, 10, -20), (-50, 5, -45)], '93C5FD', 5)
        cv.cyl(-50, 5, -62, -45, 7, '64748B', bands=((-60, -50, 'CBD5E1'),))
        cv.tube([(31, 52, 60), (20, 40, 58), (8, 30, 54)], 'FCA5A5', 3.5)
    if dims:
        cv.dim((-28, 60, 0), (-28, 60, 210), '≈ 210 mm', (-46, 40))
        cv.dim((30, -10, -4), (90, -10, -4), 'Ø 60 mm', (6, 22))
    if markers:
        m = cv.marker
        m(1, (wx, wy - 4, 210 + tz), -60, -30)
        m(2, (wx - 8, wy - 9, zc(158, 40)), -100, -25)
        m(3, (wx - 18, wy, zc(125, 20)), -90 if E == 0 else 80, 0 if E == 0 else -40)
        m(4, (wx - 17, wy, zc(60, -5)), -90, 0)
        m(5, (wx - 16, wy - 15, zc(37, -40)), -80, 25)
        m(6, (wx + 10, wy - 10, zc(25, -40)), 20, 70)
        m(7, (-50, 5, -55) if E == 0 else (wx - 14, wy - 10, zc(12, -40)), -40, 30)
        m(8, (8, 30, 54) if E == 0 else (wx - 17, wy + 10, zc(60, -5)), -60, -20)
        m(9, (SP[0] + 9 + sx, SP[1], zc(45, -10)), 70, 30)
        m(10, (74 + sx, 48, zc(100, 10)), 80, 10)
        m(11, (90.8 + shx, 60, 140), 70 if E == 0 else -40, -20 if E == 0 else -60)
        m(12, (90.6 + shx, 60, 20), 70 if E == 0 else -50, 25)
        if E > 0:
            m(5, (wx + 5, wy - 6, zc(174, 55)), 60, 0)
        cv.draw_markers()

def fit(W, H, zmin, zmax, xmin=-60, xmax=120, ymin=0, ymax=YMAX, margin=40):
    xs = []; ys = []
    for x in (xmin, xmax):
        for y in (ymin, ymax):
            for z in (zmin, zmax):
                yy = YMAX - y; xs.append((x - yy) * C30); ys.append((x + yy) * S30 - z)
    sc = min((W - 2 * margin) / (max(xs) - min(xs)), (H - 2 * margin) / (max(ys) - min(ys)))
    ox = (W - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
    oy = (H - (max(ys) - min(ys)) * sc) / 2 - min(ys) * sc
    return Cap(W, H, sc, ox, oy)

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    cv = fit(1000, 1250, -65, 215, margin=30); capsule(cv); cv.save(os.path.join(out, 'cap_hero.png'))
    cv = fit(1000, 1250, -65, 215, margin=110); capsule(cv, markers=True, dims=True); cv.save(os.path.join(out, 'cap_assembly.png'))
    cv = fit(1000, 1300, -40, 300, xmin=-75, xmax=150, margin=110); capsule(cv, E=1.0, markers=True); cv.save(os.path.join(out, 'cap_exploded.png'))
    print('ok')
