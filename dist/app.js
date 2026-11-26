const $ = id => document.getElementById(id);
const historyKey = 'reading-room-history-v1';
const recentLimit = 12;
const sentencesById = new Map(DATA.sentences.map(sentence => [sentence.id, sentence]));
const grammarById = new Map(DATA.grammar.map(point => [point.id, point]));
const wordByHanzi = new Map([...DATA.foundation, ...DATA.words].map(word => [word.hanzi, word]));
let pinyinMode = false;
let chapter = 7;
let focusChapter = false;
let current = null;
let pool = [];
let seen = new Set();
let recent = [];
try {
  const savedChapter = Number(localStorage.getItem('reading-chapter'));
  if (Number.isInteger(savedChapter) && savedChapter >= 1 && savedChapter <= 15) {
    chapter = savedChapter;
  }
  focusChapter = localStorage.getItem('reading-focus-chapter') === 'true';
  const saved = JSON.parse(localStorage.getItem(historyKey));
  if (Array.isArray(saved?.seen)) seen = new Set(saved.seen.filter(id => sentencesById.has(id)));
  if (Array.isArray(saved?.recent)) {
    recent = saved.recent.filter(id => sentencesById.has(id)).slice(0, recentLimit);
  }
} catch {
  // Storage can be unavailable, including in some browsers' offline mode.
}

function saveHistory() {
  try {
    localStorage.setItem(historyKey, JSON.stringify({ seen: [...seen], recent }));
  } catch {
    // The session can still continue with its in-memory history.
  }
}

function chooseSentence() {
  let unseen = pool.filter(sentence => !seen.has(sentence.id));
  if (!unseen.length) {
    for (const sentence of pool) seen.delete(sentence.id);
    unseen = pool;
  }

  const recentIds = new Set(recent);
  const previous = sentencesById.get(recent[0]);
  const recentFamilies = new Set(recent.slice(0, 3).map(id => sentencesById.get(id).family));
  const previousGrammar = new Set(previous?.grammarIds);
  const alternatives = unseen.filter(sentence => sentence.id !== previous?.id);
  const older = alternatives.filter(sentence => !recentIds.has(sentence.id));
  const varied = older.filter(sentence => !recentFamilies.has(sentence.family)
    && sentence.grammarIds.every(id => !previousGrammar.has(id)));
  const options = [varied, older, alternatives, unseen].find(list => list.length);
  return options?.[Math.floor(Math.random() * options.length)];
}

function setHint(button, panel, title, visible) {
  $(panel).hidden = !visible;
  $(button).setAttribute('aria-expanded', String(visible));
  $(button).textContent = (visible ? 'Hide ' : 'Show ') + title;
}

function renderPattern() {
  const details = $('pattern');
  details.open = false;
  details.hidden = !current.grammarIds.length;
  $('pattern-content').replaceChildren();
  for (const id of current.grammarIds) {
    const point = grammarById.get(id);
    const form = document.createElement('strong');
    form.textContent = point.form;
    const explanation = document.createElement('p');
    explanation.textContent = point.explanation;
    const source = document.createElement('small');
    const pageLabel = point.printedPages.length === 1 ? 'p.' : 'pp.';
    source.textContent = 'Chapter ' + point.chapter + ' · ' + pageLabel + ' '
      + point.printedPages.join(', ') + (current.generated ? ' · Generated practice example' : '');
    $('pattern-content').append(form, explanation, source);
  }
}

function showWord(token, button) {
  document.querySelectorAll('#sentence button').forEach(item => item.classList.remove('selected'));
  button.classList.add('selected');
  const word = wordByHanzi.get(token);
  const help = $('wordhelp');
  help.replaceChildren();
  const strokeButton = document.createElement('button');
  strokeButton.type = 'button';
  strokeButton.className = 'stroke-trigger';
  strokeButton.textContent = token;
  strokeButton.setAttribute('lang', 'zh-Hans');
  strokeButton.setAttribute('aria-label', 'Show stroke order for ' + token);
  strokeButton.setAttribute('aria-haspopup', 'dialog');
  const strokeImages = prepareStrokes(token);
  strokeButton.onclick = () => {
    $('stroke-word').textContent = token;
    $('stroke-images').replaceChildren(...strokeImages);
    $('stroke-popup').showModal();
  };
  help.append(strokeButton);
  help.append(document.createTextNode(word
    ? ' · ' + word.pinyin + ' · ' + word.english
    : ' — use the full-sentence hints for help.'));
  help.hidden = false;
}

function prepareStrokes(word) {
  return (word.match(/\p{Script=Han}/gu) ?? []).map(character => {
    const image = document.createElement('img');
    image.alt = 'Animated stroke order for ' + character;
    image.width = 160;
    image.height = 160;
    image.src = 'strokes/' + character.codePointAt(0).toString(16) + '.gif';
    image.decode().catch(() => {});
    return image;
  });
}

function renderSentence() {
  const sentence = $('sentence');
  const toggle = $('pinyin-mode');
  const scriptHint = $('py');
  sentence.setAttribute('lang', pinyinMode ? 'zh-Latn-pinyin' : 'zh-Hans');
  toggle.setAttribute('aria-pressed', String(pinyinMode));
  toggle.disabled = !current;
  scriptHint.disabled = !current;
  $('en').disabled = !current;
  setHint('py', 'pinyin', pinyinMode ? 'Hanzi' : 'pinyin', false);
  $('wordhelp').hidden = true;
  sentence.replaceChildren();
  if (!current) {
    sentence.textContent = 'No sentences available.';
    return;
  }

  let needsSpace = false;
  for (const token of current.tokens) {
    if (/^[\p{P}\p{Z}]+$/u.test(token)) {
      sentence.append(document.createTextNode(token));
    } else {
      if (pinyinMode && needsSpace) sentence.append(document.createTextNode(' '));
      const button = document.createElement('button');
      const prompt = pinyinMode ? wordByHanzi.get(token)?.pinyin ?? token : token;
      button.textContent = prompt;
      button.setAttribute('aria-label', prompt + ' — show word help');
      button.onclick = () => showWord(token, button);
      sentence.append(button);
      needsSpace = true;
    }
  }

  $('pinyin').textContent = pinyinMode ? current.hanzi : current.pinyin;
  $('pinyin').setAttribute('lang', pinyinMode ? 'zh-Hans' : 'zh-Latn-pinyin');
}

function next() {
  current = chooseSentence();
  setHint('en', 'english', 'English', false);
  renderSentence();
  if (!current) {
    $('pattern').hidden = true;
    return;
  }

  seen.add(current.id);
  recent = [current.id, ...recent.filter(id => id !== current.id)].slice(0, recentLimit);
  saveHistory();
  $('english').textContent = current.english;
  renderPattern();
  $('status').textContent = 'New sentence. Chapters 1 through ' + chapter;
  const remaining = pool.filter(sentence => !seen.has(sentence.id)).length;
  $('pool').textContent = pool.length.toLocaleString() + ' practice sentences · '
    + remaining.toLocaleString() + ' unseen in this round';
}

function normalize(text) {
  return text.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '');
}

function bank() {
  const query = normalize($('search').value);
  const words = DATA.words.filter(word => word.chapter <= chapter);
  $('wordcount').textContent = ' · ' + words.length + ' words';
  $('words').replaceChildren();
  for (const word of words) {
    const fields = [word.hanzi, word.pinyin, word.english];
    if (!normalize(fields.join(' ')).includes(query)) continue;
    const row = document.createElement('tr');
    for (const value of [...fields, word.chapter]) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.append(cell);
    }
    $('words').append(row);
  }

  $('downloads').replaceChildren();
  for (let number = 1; number <= chapter; number++) {
    const link = document.createElement('a');
    link.href = 'chapters/chapter-' + String(number).padStart(2, '0') + '.md';
    link.download = '';
    link.textContent = 'Chapter ' + number + ' notes';
    $('downloads').append(link);
  }
}

function update() {
  $('chapter').value = chapter;
  $('chapter').setAttribute('aria-valuetext', 'Chapters 1 through ' + chapter);
  $('value').innerHTML = chapter + ' <span>/ 15</span>';
  $('focus-chapter').checked = focusChapter;
  $('coverage').textContent = focusChapter
    ? 'Every sentence uses at least one word introduced in chapter ' + chapter + '.'
    : 'Using vocabulary and grammar from chapters 1–' + chapter + ', plus HSK 1 basics.';
  const chapterWords = new Set(DATA.words.filter(word => word.chapter === chapter).map(word => word.hanzi));
  pool = DATA.sentences.filter(sentence => sentence.minimumChapter <= chapter
    && (!focusChapter || sentence.tokens.some(token => chapterWords.has(token))));
  bank();
  next();
  try {
    localStorage.setItem('reading-chapter', chapter);
    localStorage.setItem('reading-focus-chapter', String(focusChapter));
  } catch {
    // Chapter selection is still available for this visit.
  }
}

$('chapter').oninput = event => {
  chapter = Number(event.target.value);
  update();
};
$('focus-chapter').onchange = event => {
  focusChapter = event.target.checked;
  update();
};
$('next').onclick = next;
$('search').oninput = bank;
$('reset-history').onclick = () => {
  seen.clear();
  recent = current ? [current.id] : [];
  next();
  $('status').textContent = 'Practice history reset. A new sentence is ready.';
};

$('pinyin-mode').onclick = () => {
  pinyinMode = !pinyinMode;
  renderSentence();
};
$('py').onclick = () => setHint('py', 'pinyin', pinyinMode ? 'Hanzi' : 'pinyin', $('pinyin').hidden);
$('en').onclick = () => setHint('en', 'english', 'English', $('english').hidden);
$('stroke-popup').onclick = event => {
  if (event.target === $('stroke-popup')) $('stroke-popup').close();
};
document.addEventListener('keydown', event => {
  if ($('stroke-popup').open) return;
  if (event.code === 'Space' && !event.repeat
      && !event.target.closest('button,input,textarea,select,summary,a,[contenteditable=true]')) {
    event.preventDefault();
    next();
  }
  if (event.key === 'Escape') $('wordhelp').hidden = true;
});
document.querySelector('header a').onclick = () => { $('bank').open = true; };
update();
