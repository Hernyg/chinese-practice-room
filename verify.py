from pathlib import Path
import json,re
p=Path(__file__).parent
s=(p/'dist/data.js').read_text(encoding='utf-8')
d=json.loads(s.removeprefix('const DATA = ').removesuffix(';'))
assert len(list((p/'chapters').glob('chapter-*.md')))==15
assert set(w['chapter'] for w in d['words'])==set(range(1,16))
lookup={w['hanzi']:w for w in d['foundation']+d['words']}
assert len({s['id'] for s in d['sentences']})==len(d['sentences'])
assert len({re.sub(r'[\s，。！？、,.!?]','',s['hanzi']) for s in d['sentences']})==len(d['sentences'])
grammar={g['id']:g for g in d['grammar']}
assert len(grammar)==44
assert set(grammar)=={g for s in d['sentences'] if s['generated'] for g in s['grammarIds']}
assert all(s['minimumChapter']>=14 for s in d['sentences'] if 'c14-guo' in s['grammarIds'])
assert not json.loads((p/'validation.json').read_text(encoding='utf-8'))['excluded']
for s in d['sentences']:
 assert ''.join(s['tokens'])==s['hanzi'],s['id']
 assert not re.search('[\u4e00-\u9fff]',s['english']),('Chinese leaked into English',s['id'])
 assert all(t in lookup or not re.search('[\u4e00-\u9fff]',t) for t in s['tokens']),s['id']
 assert all(s['minimumChapter']>=grammar[g]['chapter'] for g in s.get('grammarIds',[]))
 assert s['minimumChapter']>=max([lookup[t]['chapter'] for t in s['tokens'] if t in lookup]+[s['chapter']])
used={t for s in d['sentences'] for t in s['tokens']}
assert not [w['hanzi'] for w in d['words'] if w['hanzi'] not in used], 'Vocabulary lacks sentence coverage'
for n in range(1,16):
 pool=[s for s in d['sentences'] if s['minimumChapter']<=n]
 assert pool
 assert sum(s['minimumChapter']==n and s.get('generated') for s in d['sentences'])>=150,f'Too few generated sentences at chapter {n}'
 assert all(lookup[t]['chapter']<=n for s in pool for t in s['tokens'] if t in lookup)
 assert any(s['chapter']==n for s in pool),f'No usable sentences introduced in chapter {n}'
print(f"PASS: 15 chapter files, {len(d['words'])} textbook vocabulary entries, {len(d['sentences'])} sentences with all 44 textbook grammar patterns; cumulative constraints verified at all 15 slider positions.")

# Writing data must preserve complete, precomposed pinyin in every lesson.
import unicodedata
import zipfile
from writing_vocab import load_writing_lessons
writing = json.loads((p/'dist/writing-data.js').read_text(encoding='utf-8').removeprefix('const WRITING_LESSONS = ').removesuffix(';'))
assert writing == load_writing_lessons(p/'chapters')
assert [lesson['number'] for lesson in writing] == list(range(1, 16))
for lesson in writing:
 for word in lesson['words']:
  value = word['pinyin']
  assert value and value == value.strip() and '  ' not in value, word
  assert unicodedata.normalize('NFC', value) == value, word
  assert not any(unicodedata.category(c).startswith('M') or c.isdigit() or c == '\ufffd' for c in value), word
assert next(word['pinyin'] for lesson in writing for word in lesson['words'] if word['hanzi'] == '找') == 'zhǎo'
with zipfile.ZipFile(p/'dist/reading-room-offline.zip') as archive:
 assert archive.testzip() is None
 for name in ['writing.html', 'writing.css', 'writing.js', 'writing-data.js', 'style.css']:
  expected = (p/'dist'/name).read_bytes()
  if name.endswith('.html'): expected = expected.replace(b'\r\n', b'\n').replace(b'href="./?v=', b'href="index.html?v=')
  assert archive.read(name) == expected, name
 reading_characters = set(re.findall(r'[\u4e00-\u9fff]', ''.join(s['hanzi'] for s in d['sentences'])))
 for character in reading_characters:
  name = f'strokes/{ord(character):x}.gif'
  gif = archive.read(name)
  assert gif.startswith((b'GIF87a', b'GIF89a')) and gif == (p/'dist'/name).read_bytes(), character
print(f'PASS: matching offline stroke-order GIFs for all {len(reading_characters)} Reading characters.')
print(f"PASS: {sum(len(lesson['words']) for lesson in writing)} writing words: NFC pinyin, source consistency, and matching offline assets.")

from html.parser import HTMLParser
class PracticeNavigation(HTMLParser):
 def __init__(self):
  super().__init__(); self.in_nav = False; self.links = []
 def handle_starttag(self, tag, attrs):
  attrs = dict(attrs)
  if tag == 'nav' and attrs.get('aria-label') == 'Practice activities': self.in_nav = True
  if self.in_nav and tag == 'a': self.links.append(attrs)
 def handle_endtag(self, tag):
  if tag == 'nav': self.in_nav = False
menus = []
for name in ['index.html', 'writing.html']:
 menu = PracticeNavigation(); menu.feed((p/'dist'/name).read_text(encoding='utf-8'))
 assert len(menu.links) == 2
 assert sum(link.get('aria-current') == 'page' for link in menu.links) == 1
 assert all('?v=' in link['href'] for link in menu.links)
 menus.append([link['href'] for link in menu.links])
assert menus[0] == menus[1], 'Both pages must offer identical practice destinations'
assert menus[0][0].startswith('./?'), 'Reading must bypass the index.html permanent redirect'
print('PASS: consistent, versioned navigation on reading and writing pages.')
