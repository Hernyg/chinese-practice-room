from pathlib import Path
import re
import unicodedata


def load_writing_lessons(chapters: Path):
    lessons = []
    for chapter in sorted(chapters.glob('chapter-*.md')):
        number = int(chapter.stem.split('-')[1])
        text = chapter.read_text(encoding='utf-8')
        heading = text.splitlines()[0].split(' — ', 1)[1]
        vocabulary = re.split(r'^## ', text.split('## New Words\n', 1)[1], maxsplit=1, flags=re.M)[0]
        words = []
        for line in vocabulary.splitlines():
            if not re.match(r'^\|\s*\d+\s*\*?\s*\|', line):
                continue
            _, hanzi, pinyin, english, *_ = (cell.strip().replace('*', '') for cell in line.strip('|').split('|'))
            # The book lists 出 as an unnumbered subentry under 出院.
            if number == 2 and hanzi == '出':
                continue
            pinyin = unicodedata.normalize('NFC', pinyin)
            words.append(dict(hanzi=hanzi, pinyin=pinyin, english=english))
        lessons.append(dict(number=number, title=heading.split(' (', 1)[0], words=words))
    return lessons
