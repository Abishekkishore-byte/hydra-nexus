"""Conceptual CAD-style isometric illustrations of the proposed Hydra Nexus unit (PIL, supersampled).
Outputs: hero.png (no markers), iso_assembly.png (numbered markers), exploded.png (numbered markers).
All geometry is a design concept in millimetres, not a native CAD model."""
import math, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SS = 3  # supersampling
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))

def hexc(h, a=255):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

def shade(c, k):
    return tuple([max(0, min(255, int(v * k))) for v in c[:3]] + [c[3]])

class Canvas:
    def __init__(self, W, H, scale, ox, oy):
        self.W, self.H = W, H
        self.img = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
        self.s = scale * SS; self.ox = ox * SS; self.oy = oy * SS
        self.markers = []

    def P(self, x, y, z):
        y = 420 - y  # y=0 is the FRONT of the unit (nearest the viewer)
        X = (x - y) * C30 * self.s + self.ox
        Y = ((x + y) * S30 - z) * self.s + self.oy
        return (X, Y)

    def poly(self, pts3, fill, outline=None, w=1.0):
        ov = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        pts = [self.P(*p) for p in pts3]
        d.polygon(pts, fill=fill)
        if outline:
            d.line(pts + [pts[0]], fill=outline, width=max(1, int(w * SS)), joint='curve')
        self.img.alpha_composite(ov)

    def box(self, x0, y0, z0, x1, y1, z1, col, edge=None, alpha=255, top_k=1.12, left_k=0.92, right_k=0.78):
        c = hexc(col, alpha)
        e = edge or shade(hexc(col), 0.55)
        # visible faces: top (z1), front-left (y=y1 face? ) -> with this projection viewer looks from +x+y side
        self.poly([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], shade(c, left_k), e)   # front face y=y0
        self.poly([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], shade(c, right_k), e)  # face x=x1 (right-front)
        self.poly([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], shade(c, top_k), e)    # top

    def ellipse_pts(self, cx, cy, z, r, n=48, a0=0, a1=360):
        return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)), z)
                for a in [a0 + (a1 - a0) * i / n for i in range(n + 1)]]

    def cyl(self, cx, cy, z0, z1, r, col, alpha=255, edge=None, top_col=None, bands=()):
        c = hexc(col, alpha)
        e = edge or shade(hexc(col), 0.5)
        # silhouette: front half of ellipse (angles where outward normal points to viewer: +x+y => 45deg)
        front = self.ellipse_pts(cx, cy, z0, r, 40, -135, 45)
        back = self.ellipse_pts(cx, cy, z1, r, 40, 45, -135)
        # body shaded in vertical strips for a cylinder look
        n = 24
        for i in range(n):
            a0 = -135 + 180 * i / n; a1 = -135 + 180 * (i + 1) / n
            k = 0.70 + 0.42 * math.sin(math.radians((a0 + a1) / 2 + 45)) ** 0.8 if (a0 + a1) / 2 + 45 > 0 else 0.7
            ang = math.radians((a0 + a1) / 2)
            light = 0.72 + 0.38 * max(0, math.cos(ang - math.radians(-20)))
            pts = [(cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)), z0),
                   (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)), z0),
                   (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)), z1),
                   (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)), z1)]
            self.poly(pts, shade(c, light))
        for (bz0, bz1, bcol) in bands:
            for i in range(n):
                a0 = -135 + 180 * i / n; a1 = -135 + 180 * (i + 1) / n
                ang = math.radians((a0 + a1) / 2)
                light = 0.72 + 0.38 * max(0, math.cos(ang - math.radians(-20)))
                bc = hexc(bcol, alpha)
                pts = [(cx + r * 1.01 * math.cos(math.radians(a0)), cy + r * 1.01 * math.sin(math.radians(a0)), bz0),
                       (cx + r * 1.01 * math.cos(math.radians(a1)), cy + r * 1.01 * math.sin(math.radians(a1)), bz0),
                       (cx + r * 1.01 * math.cos(math.radians(a1)), cy + r * 1.01 * math.sin(math.radians(a1)), bz1),
                       (cx + r * 1.01 * math.cos(math.radians(a0)), cy + r * 1.01 * math.sin(math.radians(a0)), bz1)]
                self.poly(pts, shade(bc, light))
        # outline silhouette
        d = ImageDraw.Draw(self.img)
        sil = [self.P(*p) for p in front] + [self.P(*p) for p in back]
        d.line(sil + [sil[0]], fill=e, width=max(1, int(1.0 * SS)))
        tc = hexc(top_col, alpha) if top_col else shade(c, 1.15)
        self.poly(self.ellipse_pts(cx, cy, z1, r), tc, e)

    def tube(self, pts3, col, w=5.0):
        d = ImageDraw.Draw(self.img)
        pts = [self.P(*p) for p in pts3]
        d.line(pts, fill=shade(hexc(col), 0.55), width=int((w + 2) * SS), joint='curve')
        d.line(pts, fill=hexc(col), width=int(w * SS), joint='curve')
        hl = [(p[0] - 0.8 * SS, p[1] - 0.8 * SS) for p in pts]
        d.line(hl, fill=(255, 255, 255, 90), width=max(1, int(w * 0.3 * SS)), joint='curve')

    def dashed(self, a3, b3, col='94A3B8', w=1.4, dash=7):
        d = ImageDraw.Draw(self.img)
        a = self.P(*a3); b = self.P(*b3)
        L = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L / (dash * SS))
        for i in range(0, n, 2):
            t0 = i / n; t1 = min(1, (i + 1) / n)
            d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)],
                   fill=hexc(col), width=int(w * SS))

    def marker(self, n, at3, dx, dy):
        self.markers.append((n, at3, dx, dy))

    def draw_markers(self):
        d = ImageDraw.Draw(self.img)
        f = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', int(13 * SS))
        for n, at3, dx, dy in self.markers:
            a = self.P(*at3); b = (a[0] + dx * SS, a[1] + dy * SS)
            d.line([a, b], fill=hexc('0F172A'), width=int(1.3 * SS))
            d.ellipse([a[0] - 2.5 * SS, a[1] - 2.5 * SS, a[0] + 2.5 * SS, a[1] + 2.5 * SS], fill=hexc('0F172A'))
            R = 11 * SS
            d.ellipse([b[0] - R, b[1] - R, b[0] + R, b[1] + R], fill=hexc('0368A1'), outline=(255, 255, 255, 255), width=int(1.5 * SS))
            t = str(n); tw = d.textlength(t, font=f)
            d.text((b[0] - tw / 2, b[1] - 8 * SS), t, font=f, fill=(255, 255, 255, 255))

    def save(self, path, shadow=True, bg=None):
        img = self.img
        if shadow:
            a = img.getchannel('A').point(lambda v: 60 if v > 0 else 0)
            sh = Image.new('RGBA', img.size, (15, 23, 42, 0)); sh.putalpha(a)
            sh = sh.filter(ImageFilter.GaussianBlur(10 * SS))
            base = Image.new('RGBA', img.size, (0, 0, 0, 0))
            base.alpha_composite(sh, (int(8 * SS), int(10 * SS)))
            base.alpha_composite(img)
            img = base
        img = img.resize((self.W, self.H), Image.LANCZOS)
        if bg:
            b = Image.new('RGBA', img.size, hexc(bg)); b.alpha_composite(img); img = b
        img.save(path)

# ---------------------------------------------------------------- model
WATER_RAW = '3B82F6'; WATER_OK = '14B8A6'

def draw_unit(cv, ex=0.0, markers=False):
    """ex: explode factor 0..1. y=0 is the front of the unit."""
    E = ex
    cv.box(0, 0, 0, 720, 400, 18, 'CBD5E1')                  # base plate
    cv.box(0, 370, 18, 720, 392, 800, 'E2E8F0')              # back panel
    for x in (0, 700):
        cv.box(x, 350, 18, x + 20, 370, 800, '94A3B8')       # uprights
    # valve manifold V1-V6 on back panel, above raw tank, 2 rows x 3
    vy = -60 * E
    cv.box(40, 360 + vy, 395, 205, 368 + vy, 520, '94A3B8')  # mounting plate
    for r_ in range(2):
        for c_ in range(3):
            vx = 52 + c_ * 52; vz = 405 + r_ * 62
            cv.box(vx, 335 + vy, vz, vx + 36, 360 + vy, vz + 30, '334155')
            cv.cyl(vx + 18, 347 + vy, vz + 30, vz + 50, 10, '1E293B')
    # filter housings (wall-hung): F1 sediment, F2 carbon, F3 fine/membrane
    fx = [(290, 'F1F5F9', '0EA5E9'), (400, '93C5FD', '1D4ED8'), (510, 'BAE6FD', '0369A1')]
    for i, (x, bowl, head) in enumerate(fx):
        drop = 190 * E
        cv.box(x - 52, 345, 610, x + 52, 370, 640, '64748B')
        cv.cyl(x, 310, 588, 640, 52, head)
        if E > 0:
            cart = 'F8FAFC' if i == 0 else ('1F2937' if i == 1 else 'E0F2FE')
            cv.cyl(x, 310, 345 - drop * 0.45, 575 - drop * 0.45, 30, cart)
            cv.dashed((x, 310, 588), (x, 310, 330 - drop))
        cv.cyl(x, 310, 330 - drop, 585 - drop, 46, bowl, alpha=225)
    cv.cyl(620, 315, 360, 620, 24, 'E9D5FF', alpha=230, bands=((360, 380, '7C3AED'), (600, 620, '7C3AED')))  # optional UV-C
    # electronics enclosure (dry zone) + drip shield
    ez = 230 * E
    cv.box(380, 300, 650, 700, 372, 662, '94A3B8')
    cv.box(400, 300, 670 + ez, 690, 368, 790 + ez, 'E5E7EB')
    cv.poly([(430, 299.5, 715 + ez), (530, 299.5, 715 + ez), (530, 299.5, 768 + ez), (430, 299.5, 768 + ez)], hexc('0F172A'))
    cv.poly([(437, 299, 722 + ez), (523, 299, 722 + ez), (523, 299, 761 + ez), (437, 299, 761 + ez)], hexc('0EA5E9'))
    cv.cyl(650, 300 - 6, 735 + ez, 760 + ez, 12, 'DC2626')  # E-stop (front face)
    for k in range(4):
        cv.cyl(560 + k * 26, 330, 660 + ez, 670 + ez, 6, '1F2937')  # bottom cable glands
    # raw-water tank (left front)
    ty = -150 * E
    cv.box(25, 40 + ty, 18, 175, 300 + ty, 230, WATER_RAW, alpha=170)
    cv.box(20, 35 + ty, 18, 180, 305 + ty, 340, 'DBEAFE', alpha=95, edge=hexc('60A5FA'))
    cv.box(20, 35 + ty, 340, 180, 305 + ty, 350, '60A5FA', alpha=230)
    # treated-water tank (right front)
    cv.box(575, 40 - 150 * E, 18, 700, 250 - 150 * E, 200, WATER_OK, alpha=170)
    cv.box(570, 35 - 150 * E, 18, 705, 255 - 150 * E, 290, 'CCFBF1', alpha=95, edge=hexc('2DD4BF'))
    cv.box(570, 35 - 150 * E, 290, 705, 255 - 150 * E, 300, '2DD4BF', alpha=230)
    # sensor chambers + probes, pump between them (front row)
    def chamber(cx, cy, col):
        lift = 90 * E
        cv.cyl(cx, cy, 18, 40, 50, '94A3B8')
        cv.cyl(cx, cy, 40, 200, 42, col, alpha=150)
        cv.cyl(cx, cy, 200, 214, 46, '475569')
        for (pdx, pdy, pc, pr, ph) in ((-15, 14, '111827', 6, 120), (15, 14, 'F8FAFC', 5, 95), (-15, -14, '1F2937', 9, 70), (15, -14, 'CBD5E1', 3, 110)):
            cv.cyl(cx + pdx, cy + pdy, 214 + lift, 214 + lift + ph * 0.6, pr, pc)
    cy0 = 95 - 120 * E
    chamber(250, cy0, WATER_RAW)
    px0 = 325; py0 = 60 - 150 * E
    cv.box(px0, py0, 18, px0 + 110, py0 + 80, 32, '475569')
    cv.box(px0 + 8, py0 + 8, 32, px0 + 64, py0 + 72, 105, '1F2937')
    cv.cyl(px0 + 86, py0 + 40, 32, 100, 24, '64748B')
    chamber(510, cy0, WATER_OK)
    if E == 0:
        cv.tube([(180, 160, 40), (300, 160, 40), (330, 110, 40)], WATER_RAW)                        # tank -> pump
        cv.tube([(411, 100, 100), (330, 60, 160), (265, 80, 214)], WATER_RAW)                        # pump -> S1
        cv.tube([(235, 110, 214), (210, 300, 380), (175, 335, 420)], WATER_RAW)                      # S1 -> manifold
        cv.tube([(120, 335, 525), (200, 340, 640), (290, 340, 640)], WATER_RAW, 4)                  # manifold -> F1
        cv.tube([(290, 340, 640), (400, 340, 640)], '60A5FA', 4)
        cv.tube([(400, 340, 640), (510, 340, 640)], '22D3EE', 4)
        cv.tube([(510, 340, 640), (620, 330, 620)], WATER_OK, 4)
        cv.tube([(620, 300, 360), (560, 170, 230), (520, 110, 214)], WATER_OK)                        # UV -> S2
        cv.tube([(495, 80, 214), (560, 60, 310), (620, 130, 300)], WATER_OK)                          # S2 -> tank
    if markers:
        z = 230 * E
        cv.marker(1, (20, 120 - 150 * E, 300), -55, 25)
        cv.marker(2, (250, cy0 - 40, 140), -95, 55)
        cv.marker(3, (px0 + 40, py0, 70), -40, 95)
        cv.marker(4, (110, 340 - 60 * E, 470), -110, -50)
        cv.marker(5, (290, 270, 470 - 190 * E), -45 if not E else -110, -175 if not E else -70)
        cv.marker(6, (400, 270, 470 - 190 * E), -40, -190 if not E else -120)
        cv.marker(7, (510, 270, 470 - 190 * E), 25, -215 if not E else -140)
        cv.marker(8, (630, 300, 520), 95 if not E else 80, -40 if not E else 70)
        cv.marker(9, (510, cy0 - 40, 140), 30, 95)
        cv.marker(10, (705, 120 - 150 * E, 240), 70, 30)
        cv.marker(11, (690, 330, 770 + z), 75, -25)
        cv.marker(12, (700, 340, 656), 80 if not E else 60, 35 if not E else -70)
        cv.draw_markers()

def fit(W, H, ex=0.0, margin=40):
    xs=[];ys=[]
    for x in (0,720):
        for y in (-140*ex,400):
            for z in (0,800+230*ex):
                yy=420-y; xs.append((x-yy)*C30); ys.append((x+yy)*S30-z)
    sc=min((W-2*margin)/(max(xs)-min(xs)),(H-2*margin)/(max(ys)-min(ys)))
    ox=(W-(max(xs)-min(xs))*sc)/2-min(xs)*sc; oy=(H-(max(ys)-min(ys))*sc)/2-min(ys)*sc
    return Canvas(W,H,sc,ox,oy)

if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    cv = fit(1000, 1000, 0, 30); draw_unit(cv); cv.save(os.path.join(out, 'hero.png'))
    cv = fit(1000, 1000, 0, 90); draw_unit(cv, markers=True); cv.save(os.path.join(out, 'iso_assembly.png'))
    cv = fit(1000, 1000, 1.0, 90); draw_unit(cv, ex=1.0, markers=True); cv.save(os.path.join(out, 'exploded.png'))
    print('ok')
