"""Generate stroke-order assets from the pinned Hanzi Writer Data tarball."""
from pathlib import Path
import json
import re
import sys
import tarfile

from PIL import Image, ImageDraw
from fontTools.misc.bezierTools import cubicPointAtT, quadraticPointAtT
from fontTools.pens.basePen import BasePen
from fontTools.svgLib.path import parse_path

from writing_vocab import load_writing_lessons


class StrokeOutline(BasePen):
    def __init__(self):
        super().__init__(None)
        self.polygons = []
        self.points = []

    def _moveTo(self, point):
        self.points = [point]

    def _lineTo(self, point):
        self.points.append(point)

    def _curveToOne(self, first, second, end):
        start = self.points[-1]
        self.points.extend(cubicPointAtT(start, first, second, end, step / 18)
                           for step in range(1, 19))

    def _qCurveToOne(self, control, end):
        start = self.points[-1]
        self.points.extend(quadraticPointAtT(start, control, end, step / 14)
                           for step in range(1, 15))

    def _closePath(self):
        self.polygons.append(self.points)
        self.points = []

    _endPath = _closePath


def draw_character(paths, output, save_static=True):
    canvas = 320
    outlines = []
    for path in paths:
        outline = StrokeOutline()
        parse_path(path, outline)
        outlines.append([[(24 + x * .265, 24 + (900 - y) * .265)
                          for x, y in polygon] for polygon in outline.polygons])

    def frame(index):
        image = Image.new('RGB', (canvas, canvas), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle((8, 8, 312, 312), outline='#d6dde3', width=2)
        draw.line((160, 8, 160, 312), fill='#eeeeee')
        draw.line((8, 160, 312, 160), fill='#eeeeee')
        for i, stroke in enumerate(outlines):
            color = '#202a35' if i < index else '#d83d36' if i == index else '#d7dce1'
            for polygon in stroke:
                draw.polygon(polygon, fill=color)
        return image.resize((160, 160), Image.Resampling.LANCZOS)

    frames = [frame(index) for index in range(-1, len(outlines) + 1)]
    if save_static:
        frames[-1].save(output.with_suffix('.png'), optimize=True)
    frames[0].save(output, save_all=True, append_images=frames[1:],
                   duration=[450] + [420] * len(outlines) + [1300], loop=0, optimize=True)


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    assets = root / 'dist' / 'strokes'
    assets.mkdir(exist_ok=True)
    writing = {character for lesson in load_writing_lessons(root / 'dist' / 'chapters')
               for word in lesson['words'] for character in word['hanzi']}
    data = (root / 'dist' / 'data.js').read_text(encoding='utf-8')
    sentences = json.loads(data.strip().removeprefix('const DATA = ').removesuffix(';'))['sentences']
    reading = {character for sentence in sentences
               for character in re.findall(r'[\u4e00-\u9fff]', sentence['hanzi'])}
    characters = sorted(writing | reading)
    with tarfile.open(sys.argv[1]) as source:
        license_text = source.extractfile('package/APL/english/ARPHICPL.TXT').read()
        (assets / 'LICENSE.txt').write_bytes(
            b'Stroke animations derived from Hanzi Writer Data 2.0.1 and Make Me a Hanzi.\n'
            b'Copyright (C) 1999 Arphic Technology Co., Ltd.\n'
            b'https://github.com/chanind/hanzi-writer-data\n\n' + license_text)
        for character in characters:
            output = assets / f'{ord(character):x}.gif'
            if output.is_file() and (character not in writing or output.with_suffix('.png').is_file()):
                continue
            data = json.load(source.extractfile(f'package/{character}.json'))
            draw_character(data['strokes'], output, save_static=character in writing)
    print(f'Generated stroke order art for {len(characters)} characters')
