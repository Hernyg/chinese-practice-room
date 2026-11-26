const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const code = ['data.js', 'app.js'].map(file =>
  fs.readFileSync(__dirname + '/dist/' + file, 'utf8')).join('\n');
const historyKey = 'reading-room-history-v1';

function launch(storage = new Map()) {
  function element() {
    return {
      hidden: false, value: '', textContent: '', innerHTML: '', children: [],
      classList: { add() {}, remove() {} },
      setAttribute(key, value) { this[key] = value; },
      replaceChildren(...items) { this.children = items; },
      append(...items) { this.children.push(...items); },
      showModal() { this.open = true; },
      close() { this.open = false; },
    };
  }

  const nodes = new Map();
  const preloadedImages = [];
  const document = {
    getElementById(id) {
      if (!nodes.has(id)) nodes.set(id, element());
      return nodes.get(id);
    },
    createElement(tag) {
      const node = element();
      if (tag === 'img') node.decode = () => {
        preloadedImages.push(node);
        return Promise.resolve();
      };
      return node;
    },
    createTextNode: text => text,
    querySelectorAll: () => [],
    querySelector: element,
    addEventListener() {},
  };
  const context = vm.createContext({
    document,
    localStorage: { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value) },
  });
  const run = source => vm.runInContext(source, context);
  run(code);
  return { nodes, run, preloadedImages };
}

const { nodes, run, preloadedImages } = launch();
assert.equal(run('chapter'), 7);
const initialId = run('current.id');
const mode = nodes.get('pinyin-mode');
const sentence = nodes.get('sentence');
const scriptHint = nodes.get('py');
const englishHint = nodes.get('en');
assert.equal(mode['aria-pressed'], 'false');
scriptHint.onclick();
mode.onclick();
assert.equal(run('current.id'), initialId);
assert.equal(mode['aria-pressed'], 'true');
assert.equal(scriptHint.textContent, 'Show Hanzi');
assert.equal(nodes.get('pinyin').hidden, true);
const firstWord = run('wordByHanzi.get(current.tokens.find(token => wordByHanzi.has(token)))');
const firstButton = sentence.children.find(item => typeof item !== 'string');
assert.equal(firstButton.textContent, firstWord.pinyin);
firstButton.onclick();
assert.equal(nodes.get('wordhelp').hidden, false);
const wordHelp = nodes.get('wordhelp');
assert.equal(wordHelp.children[0].textContent, firstWord.hanzi);
assert.ok(wordHelp.children.at(-1).includes(firstWord.english));
const popup = nodes.get('stroke-popup');
run("showWord('老师', document.createElement('button'))");
assert.equal(wordHelp.children.length, 2);
assert.equal(wordHelp.children[0].textContent, '老师');
const teacherImages = preloadedImages.slice(-2);
assert.deepEqual(teacherImages.map(image => image.src), ['strokes/8001.gif', 'strokes/5e08.gif']);
assert.ok(!popup.open);
wordHelp.children[0].onclick();
assert.equal(popup.open, true);
assert.equal(nodes.get('stroke-word').textContent, '老师');
const images = nodes.get('stroke-images');
assert.deepEqual(images.children.map(image => image.src), ['strokes/8001.gif', 'strokes/5e08.gif']);
assert.deepEqual(images.children, teacherImages);
popup.onclick({ target: images.children[0] });
assert.equal(popup.open, true);
popup.onclick({ target: popup });
assert.equal(popup.open, false);
assert.equal(wordHelp.hidden, false);
scriptHint.onclick();
assert.equal(scriptHint.textContent, 'Hide Hanzi');
assert.equal(nodes.get('pinyin').textContent, run('current.hanzi'));
assert.equal(nodes.get('english').hidden, true);
englishHint.onclick();
assert.equal(nodes.get('english').hidden, false);
nodes.get('next').onclick();
assert.equal(mode['aria-pressed'], 'true');
for (const hint of ['pinyin', 'english', 'wordhelp']) assert.equal(nodes.get(hint).hidden, true);
mode.onclick();
assert.equal(mode['aria-pressed'], 'false');
assert.equal(scriptHint.textContent, 'Show pinyin');
assert.equal(nodes.get('pinyin').textContent, run('current.pinyin'));
assert.ok(run('DATA.sentences.every(sentence => sentence.tokens.every(token => /^[\\p{P}\\p{Z}]+$/u.test(token) || Boolean(wordByHanzi.get(token)?.pinyin)))'));

for (let chapter = 1; chapter <= 15; chapter++) {
  run(`chapter = ${chapter}; update()`);
  let previous = run('current.id');
  for (let i = 0; i < 200; i++) {
    nodes.get('py').onclick();
    nodes.get('en').onclick();
    nodes.get('pattern').open = true;
    nodes.get('next').onclick();
    const result = run('current');
    assert.ok(result.minimumChapter <= chapter);
    assert.notEqual(result.id, previous);
    previous = result.id;
    assert.equal(nodes.get('pinyin').hidden, true);
    assert.equal(nodes.get('english').hidden, true);
    assert.equal(nodes.get('pattern').open, false);
    assert.equal(nodes.get('pattern').hidden, !result.grammarIds.length);
  }
}

const storage = new Map([['reading-chapter', '1']]);
let practice = launch(storage);
const poolSize = practice.run('pool.length');
const visited = new Set([practice.run('current.id')]);
for (let i = 1; i < poolSize; i++) {
  if (i === 10) {
    const slider = practice.nodes.get('chapter');
    slider.oninput({ target: { value: '7' } });
    const newId = practice.run('current.id');
    if (practice.run('current.minimumChapter') === 1) visited.add(newId);
    slider.oninput({ target: { value: '1' } });
  } else if (i === 20) {
    practice = launch(storage);
    assert.equal(practice.run('chapter'), 1);
  } else {
    practice.nodes.get('next').onclick();
  }
  const id = practice.run('current.id');
  assert.ok(!visited.has(id), 'An unseen eligible sentence should be used first');
  visited.add(id);
  if (visited.size === poolSize) break;
}
assert.equal(visited.size, poolSize);
const recentIds = new Set(practice.run('recent'));
practice.nodes.get('next').onclick();
assert.ok(!recentIds.has(practice.run('current.id')), 'A new round should avoid recent sentences');
assert.equal(practice.run('pool.filter(sentence => seen.has(sentence.id)).length'), 1);
assert.equal(JSON.parse(storage.get(historyKey)).seen.length, practice.run('seen.size'));
practice.nodes.get('next').onclick();
practice.nodes.get('reset-history').onclick();
assert.equal(practice.run('seen.size'), 1);
assert.equal(practice.run('recent.length') <= 12, true);

const focusStorage = new Map();
const focus = launch(focusStorage);
const focusSwitch = focus.nodes.get('focus-chapter');
assert.equal(focusSwitch.checked, false);
focusSwitch.onchange({ target: { checked: true } });
for (let chapter = 1; chapter <= 15; chapter++) {
  focus.nodes.get('chapter').oninput({ target: { value: String(chapter) } });
  const ids = focus.run(`
    (() => {
      const words = new Set(DATA.words.filter(word => word.chapter === chapter).map(word => word.hanzi));
      const expected = DATA.sentences.filter(sentence => sentence.minimumChapter <= chapter
        && sentence.tokens.some(token => words.has(token)));
      return [pool.map(sentence => sentence.id).join(), expected.map(sentence => sentence.id).join(), current.id];
    })()
  `);
  assert.ok(ids[0], `Chapter ${chapter} should have focused practice sentences`);
  assert.equal(ids[0], ids[1]);
  assert.ok(ids[0].split(',').includes(ids[2]));
}
const reloaded = launch(focusStorage);
assert.equal(reloaded.nodes.get('focus-chapter').checked, true);
assert.equal(reloaded.run('chapter'), 15);
reloaded.nodes.get('focus-chapter').onchange({ target: { checked: false } });
assert.equal(reloaded.run('pool.length'), reloaded.run('DATA.sentences.length'));

const corrupt = launch(new Map([[historyKey, '{invalid']]));
assert.ok(corrupt.run('current.id'));
const blocked = launch({ get() { throw new Error('blocked'); }, set() { throw new Error('blocked'); } });
const first = blocked.run('current.id');
blocked.nodes.get('next').onclick();
assert.notEqual(blocked.run('current.id'), first);
assert.equal(blocked.run('seen.size'), 2);

console.log('PASS: 3,000 chapter selections, hint resets, persistence across reload and slider changes, full-cycle exhaustion, reset, chapter focus at all 15 levels, and storage failures.');
