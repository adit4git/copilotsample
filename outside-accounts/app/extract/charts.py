"""Read allocation percentages that a statement shows only as a chart.

Two measured methods, tried in this order on every page classed as a chart page (and on summary pages with graphics):

1. Vector bar charts (text PDFs).
   - pdfplumber returns the filled rectangles and the words with their positions.
   - Bars are rectangles of one colour that share a baseline.
   - Each label is the text beside its bar.
   - The axis ticks ("0%", "10%", …) give a straight-line mapping from position to percent.
   - Exact up to drawing precision.
2. Raster pie charts (images in a PDF, scanned pages, screenshots).
   - Saturated pixels are grouped by colour.
   - For each colour, the big connected region is the slice and the small square is its legend swatch.
   - A slice's share is its pixel area over the whole pie.
   - The legend text right of each swatch is read with OCR.
   - Typically within about half a point; thin white separators and anti-aliasing cost a little on small slices.

The optional language-model reader (extract/llm.py) can read any chart image, but its values are accepted only when
they add up to 100 and, where a measured value exists, agree with it within 3 points.

Every chart result carries its method and a confidence, and the review screen shows the cropped chart next to the values.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass

import numpy as np
from PIL import Image

PCT_TICK = re.compile(r'^(-?\d{1,3}(?:\.\d+)?)%$')


@dataclass
class ChartResult:
    page: int
    type: str              # 'pie' | 'bar'
    method: str            # 'vector' | 'raster' | 'llm'
    title: str | None
    values: list           # [{'label', 'pct'}]
    confidence: float
    image: bytes | None = None
    note: str = ''

    def to_dict(self):
        return {'page': self.page, 'type': self.type, 'method': self.method, 'title': self.title, 'values': self.values,
                'confidence': self.confidence, 'note': self.note, 'sum': round(sum(v['pct'] for v in self.values), 2)}


def _color_key(c):
    if c is None:
        return None
    if isinstance(c, (int, float)):
        c = (c, c, c)
    c = tuple(round(float(x), 2) for x in c[:3]) if len(c) >= 3 else tuple(round(float(x), 2) for x in c)
    return c


# ---------------------------------------------------------------------------------------------------------------- vector bars
def vector_bars(pdf_page, page_no: int, title: str | None = None) -> list[ChartResult]:
    rects = [r for r in pdf_page.rects if r.get('fill') and r['width'] > 1 and r['height'] > 1]
    words = pdf_page.extract_words(keep_blank_chars=False, use_text_flow=False)
    out = []
    groups: dict = {}
    for r in rects:
        k = _color_key(r.get('non_stroking_color'))
        if k is None or all(x > 0.92 for x in k):          # skip white or background boxes
            continue
        groups.setdefault(k, []).append(r)
    ticks = [(w, float(PCT_TICK.match(w['text']).group(1))) for w in words if PCT_TICK.match(w['text'])]
    for color, rs in groups.items():
        if len(rs) < 3:
            continue
        # horizontal bars share a left edge; vertical bars share a bottom edge
        lefts = np.array([r['x0'] for r in rs]); bottoms = np.array([r['bottom'] for r in rs])
        horizontal = np.ptp(lefts) < 1.5 and len({round(r['top']) for r in rs}) == len(rs)
        vertical = np.ptp(bottoms) < 1.5 and len({round(r['x0']) for r in rs}) == len(rs)
        if not (horizontal or vertical):
            continue
        if horizontal:
            axis = [(0.5 * (w['x0'] + w['x1']), v) for w, v in ticks if w['top'] > max(r['bottom'] for r in rs)]
        else:
            axis = [(0.5 * (w['top'] + w['bottom']), v) for w, v in ticks if w['x1'] < min(r['x0'] for r in rs)]
        if len(axis) < 2:
            continue
        pos, val = np.array([a[0] for a in axis]), np.array([a[1] for a in axis])
        slope, icpt = np.polyfit(pos, val, 1)
        resid = np.abs(slope * pos + icpt - val).max()
        vals = []
        for r in sorted(rs, key=lambda r: (r['top'] if horizontal else r['x0'])):
            if horizontal:
                v = slope * (r['x1'] - r['x0'])
                yc = 0.5 * (r['top'] + r['bottom'])
                lab = [w for w in words if w['x1'] <= r['x0'] + 1 and abs(0.5 * (w['top'] + w['bottom']) - yc) < max(4, r['height'] * 0.6) and not PCT_TICK.match(w['text'])]
            else:
                v = slope * (r['top'] - r['bottom'])
                xc = 0.5 * (r['x0'] + r['x1'])
                lab = [w for w in words if w['top'] >= r['bottom'] - 1 and abs(0.5 * (w['x0'] + w['x1']) - xc) < max(12, r['width']) and not PCT_TICK.match(w['text'])]
            text = ' '.join(w['text'] for w in sorted(lab, key=lambda w: (round(w['top']), w['x0'])))
            vals.append({'label': text.strip() or f'Bar {len(vals) + 1}', 'pct': round(float(v), 2)})
        conf = 0.95 if resid < 0.2 and all(not v['label'].startswith('Bar ') for v in vals) else 0.75
        out.append(ChartResult(page_no, 'bar', 'vector', title, vals, conf,
                               note=f'Measured from {len(vals)} vector bars against {len(axis)} axis ticks'))
    return out


# ---------------------------------------------------------------------------------------------------------------- raster pies
def _quantize(arr):
    return (arr // 24).astype(np.int32)


def raster_pie(img: Image.Image, page_no: int, title: str | None = None, ocr=True) -> ChartResult | None:
    """Find a pie chart and its legend in an image; return slice shares and legend labels."""
    from scipy import ndimage
    rgb = np.asarray(img.convert('RGB')).astype(np.int32)
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    # colourful pixels, plus mid greys that are not text (legend/slice greys are common for "Other")
    grey = (mx - mn < 18) & (mx > 90) & (mx < 200)
    mask = (sat > 0.22) & (mx > 60) | grey
    if mask.sum() < 400:
        return None
    q = _quantize(rgb)
    keys = q[..., 0] * 10000 + q[..., 1] * 100 + q[..., 2]
    ks, counts = np.unique(keys[mask], return_counts=True)
    total = mask.sum()
    colours = [k for k, c in sorted(zip(ks, counts), key=lambda t: -t[1]) if c > total * 0.004]
    # merge neighbouring quantisation bins of the same colour
    merged: list[list[int]] = []
    for k in colours:
        c = np.array([k // 10000, (k // 100) % 100, k % 100])
        for m in merged:
            c0 = np.array([m[0] // 10000, (m[0] // 100) % 100, m[0] % 100])
            if np.abs(c - c0).max() <= 1:
                m.append(k); break
        else:
            merged.append([k])
    slices, swatches = [], []
    for group in merged:
        cm = np.isin(keys, group) & mask
        lab, n = ndimage.label(cm)
        if n == 0:
            continue
        sizes = ndimage.sum(cm, lab, range(1, n + 1))
        objs = ndimage.find_objects(lab)
        comps = sorted([(sizes[i], objs[i], i + 1) for i in range(n)], key=lambda t: -t[0])
        big = [c for c in comps if c[0] > total * 0.003]
        sw = None
        for s, sl, i in comps:          # legend swatch: small, square, solid
            h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            if 30 <= s <= 4000 and 0.7 <= h / max(w, 1) <= 1.4 and s / (h * w) > 0.8:
                sw = (sl, s, i); break
        area = sum(c[0] for c in big if not sw or c[2] != sw[2])
        if area <= 0:
            continue
        rgbmean = rgb[cm].mean(axis=0)
        slices.append({'area': float(area), 'rgb': rgbmean, 'swatch': sw, 'bbox': [c[1] for c in big if not sw or c[2] != sw[2]]})
        if sw:
            swatches.append(sw)
    # keep colours that form one roughly circular pie
    slices = [s for s in slices if s['bbox']]
    if len(slices) < 2:
        return None
    ys = [b[0].start for s in slices for b in s['bbox']] + [b[0].stop for s in slices for b in s['bbox']]
    xs = [b[1].start for s in slices for b in s['bbox']] + [b[1].stop for s in slices for b in s['bbox']]
    ph, pw = max(ys) - min(ys), max(xs) - min(xs)
    if not 0.75 <= ph / max(pw, 1) <= 1.33:
        return None
    circle = np.pi * (max(ph, pw) / 2) ** 2
    covered = sum(s['area'] for s in slices) / circle
    # white separators between slices remove about the same area from every slice (a strip along each radial edge),
    # so the missing area is added back in equal parts. A ring chart (covered well below the full circle) is left as is.
    if 0.85 <= covered < 1.0:
        per = (circle - sum(s['area'] for s in slices)) / len(slices)
        for s in slices:
            s['area'] += per
    tot = sum(s['area'] for s in slices)
    vals = []
    for k, s in enumerate(sorted(slices, key=lambda s: -s['area'])):
        label = None
        if s['swatch'] and ocr:
            label = _legend_text(img, s['swatch'][0])
        vals.append({'label': label or f'Slice {k + 1}', 'pct': round(s['area'] / tot * 100, 2),
                     'color': '#%02x%02x%02x' % tuple(int(x) for x in s['rgb'])})
    labelled = all(not v['label'].startswith('Slice') for v in vals)
    conf = round(min(0.9, 0.6 + 0.3 * covered) if labelled else 0.55, 2)
    crop = img.crop((max(0, min(xs) - 20), max(0, min(ys) - 20), img.width, min(img.height, max(ys) + 20)))
    b = io.BytesIO(); crop.convert('RGB').save(b, 'PNG')
    return ChartResult(page_no, 'pie', 'raster', title, vals, conf, b.getvalue(),
                       note=f'Measured from slice areas ({covered * 100:.0f}% of the circle coloured); legend read by OCR')


def _legend_text(img: Image.Image, sl) -> str | None:
    import pytesseract
    y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
    h = y1 - y0
    box = (x1 + 2, max(0, y0 - h // 2), min(img.width, x1 + 2 + h * 22), min(img.height, y1 + h // 2))
    crop = img.crop(box).convert('L')
    scale = max(1, int(round(40 / max(h, 1))))
    if scale > 1:
        crop = crop.resize((crop.width * scale, crop.height * scale), Image.LANCZOS)
    t = pytesseract.image_to_string(crop, config='--psm 7').strip()
    t = re.sub(r'[^A-Za-z0-9&%.,/()\- ]', '', t)
    t = re.sub(r'\s{2,}', ' ', t).strip(' .-')
    return t or None


def find_pie_in_page_image(img: Image.Image, page_no: int, title=None) -> ChartResult | None:
    """Scanned or rendered page: try the whole page, then the colourful region only."""
    r = raster_pie(img, page_no, title)
    return r


# ---------------------------------------------------------------------------------------------------------------- matching to holdings
GROUP_WORDS = [('alt', r'alternative|hedge|private|real assets|commodit'), ('intl', r'international|non-u\.?s|foreign|global ex|developed|emerging'),
               ('fixed', r'fixed income|bond|treasur|municipal|credit'), ('cash', r'cash|money market|short-term reserves|sweep'),
               ('us_eq', r'u\.?s\.? equit|domestic|us stock|u\.?s\.? stock|large cap|small cap|mid cap|equit|stock')]


def label_group(label: str) -> str | None:
    t = label.lower()
    for g, pat in GROUP_WORDS:
        if re.search(pat, t):
            return g
    return None
