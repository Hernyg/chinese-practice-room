(() => {
  const byId = id => document.getElementById(id);
  const lessonPicker = byId('lesson');
  const focusLesson = byId('focus-lesson');
  const prompt = byId('prompt');
  const answer = byId('answer');
  const revealButton = byId('reveal');
  const ratings = byId('ratings');
  const waiting = byId('waiting');
  const playButton = byId('animate');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const earlyReviewWindow = 60 * 60000;
  const intervals = [
    { label: 'Again', minutes: 1, delay: '1 min' },
    { label: 'Hard', minutes: 5, delay: '5 min' },
    { label: 'Good', minutes: 10, delay: '10 min' },
    { label: 'Easy', minutes: 1440, delay: '1 day' },
  ];
  const storageKey = 'reading-room-writing-v1';
  let saved = {};
  try {
    saved = JSON.parse(localStorage.getItem(storageKey)) || {};
  } catch {}

  let cards;
  let current;
  let revealed = false;
  let timer;

  function persist() {
    saved.lesson = Number(lessonPicker.value);
    saved.focusLesson = focusLesson.checked;
    saved.direction = direction();
    try {
      localStorage.setItem(storageKey, JSON.stringify(saved));
    } catch {}
  }

  function direction() {
    return document.querySelector('input[name="direction"]:checked').value;
  }

  function setText(element, word, side) {
    element.lang = side === 'hanzi' ? 'zh-Hans' : 'zh-Latn-pinyin';
    element.textContent = word[side].normalize('NFC');
  }

  function showPrompt() {
    revealed = false;
    prompt.classList.remove('revealed');
    answer.hidden = true;
    ratings.hidden = true;
    revealButton.setAttribute('aria-expanded', 'false');
    byId('strokes').replaceChildren();
    byId('translation').textContent = '';
    byId('meaning').textContent = '';
    if (!current) return;
    setText(prompt, current.word, direction());
    for (const character of new Set(current.word.hanzi)) {
      const preload = new Image();
      preload.src = strokeUrl(character, true);
    }
  }

  function selectCard() {
    clearTimeout(timer);
    const now = Date.now();
    const newCards = cards.filter(card => card.at === null);
    const ready = cards.filter(card => card.at !== null && card.at <= now).sort((a, b) => a.at - b.at);
    const next = Math.min(...cards.filter(card => card.at !== null).map(card => card.at));
    current = ready[0] || newCards[0];
    if (!current && next - now <= earlyReviewWindow) {
      current = cards.find(card => card.at === next);
    }
    byId('progress').textContent = `${newCards.length} new · ${ready.length} due · ${cards.length} words`;
    showPrompt();
    prompt.hidden = !current;
    revealButton.hidden = !current;
    waiting.hidden = Boolean(current);
    if (current) return;

    const minutes = Math.max(1, Math.ceil((next - now) / 60000));
    waiting.textContent = `All caught up for now. Next card in ${minutes >= 1440 ? '1 day' : minutes + ' min'}.`;
    timer = setTimeout(selectCard, Math.min(next - now - earlyReviewWindow, 60000));
  }

  function loadLessons() {
    const selected = Number(lessonPicker.value);
    const focused = focusLesson.checked;
    const scope = focused || selected === 1 ? `lesson ${selected}` : `lessons 1 through ${selected}`;
    lessonPicker.setAttribute('aria-valuetext', `Study ${scope}`);
    byId('value').firstChild.nodeValue = `${selected} `;
    byId('coverage').textContent = `Practicing words from ${scope}.`;
    cards = WRITING_LESSONS
      .filter(lesson => focused ? lesson.number === selected : lesson.number <= selected)
      .flatMap(lesson => lesson.words.map(word => {
        const at = saved.reviews?.[lesson.number]?.[word.hanzi];
        return { word, lesson: lesson.number, at: Number.isFinite(at) ? at : null };
      }));
    persist();
    selectCard();
  }

  function setReview(card, at) {
    card.at = at;
    saved.reviews ??= {};
    saved.reviews[card.lesson] ??= {};
    saved.reviews[card.lesson][card.word.hanzi] = at;
  }

  function strokeUrl(character, animated) {
    return `strokes/${character.codePointAt(0).toString(16)}.${animated ? 'gif' : 'png'}?v=2`;
  }

  function showStrokes(animated) {
    const figures = Array.from(current.word.hanzi, character => {
      const figure = document.createElement('figure');
      const image = document.createElement('img');
      const caption = document.createElement('figcaption');
      image.width = 160;
      image.height = 160;
      image.alt = `${character} stroke order`;
      image.src = strokeUrl(character, animated);
      caption.lang = 'zh-Hans';
      caption.textContent = character;
      figure.append(image, caption);
      return figure;
    });
    byId('strokes').replaceChildren(...figures);
    playButton.hidden = animated;
  }

  function reveal() {
    if (!current || revealed) return;
    revealed = true;
    prompt.classList.add('revealed');
    setText(byId('translation'), current.word, direction() === 'pinyin' ? 'hanzi' : 'pinyin');
    byId('meaning').textContent = current.word.english;
    showStrokes(!reducedMotion.matches);
    answer.hidden = false;
    ratings.hidden = false;
    revealButton.setAttribute('aria-expanded', 'true');
    revealButton.hidden = true;
    byId('flashcard').focus({ preventScroll: true });
  }

  function rate(minutes) {
    if (!revealed) return;
    setReview(current, Date.now() + minutes * 60000);
    persist();
    selectCard();
    if (current) revealButton.focus({ preventScroll: true });
    else byId('restart').focus({ preventScroll: true });
  }

  for (const { label, minutes, delay } of intervals) {
    const button = document.createElement('button');
    const interval = document.createElement('small');
    button.type = 'button';
    button.append(label, interval);
    interval.textContent = delay;
    button.addEventListener('click', () => rate(minutes));
    ratings.append(button);
  }
  if (WRITING_LESSONS.some(entry => entry.number === saved.lesson)) lessonPicker.value = saved.lesson;
  focusLesson.checked = saved.focusLesson === true;
  const directions = document.querySelectorAll('input[name="direction"]');
  if (saved.direction === 'hanzi') directions[1].checked = true;
  directions.forEach(input => input.addEventListener('change', () => {
    persist();
    selectCard();
  }));
  lessonPicker.addEventListener('input', loadLessons);
  focusLesson.addEventListener('change', loadLessons);
  revealButton.addEventListener('click', reveal);
  playButton.addEventListener('click', () => {
    showStrokes(true);
    byId('flashcard').focus({ preventScroll: true });
  });
  byId('restart').addEventListener('click', () => {
    cards.forEach(card => setReview(card, null));
    persist();
    selectCard();
    revealButton.focus({ preventScroll: true });
  });
  document.addEventListener('keydown', event => {
    if (event.repeat || event.altKey || event.ctrlKey || event.metaKey ||
        event.target.closest('select,input,textarea,[contenteditable]')) return;
    if (event.code === 'Space' && current && !revealed && !event.target.closest('button,a')) {
      event.preventDefault();
      reveal();
    }
    if (revealed && /^[1-4]$/.test(event.key)) {
      event.preventDefault();
      rate(intervals[Number(event.key) - 1].minutes);
    }
  });
  loadLessons();
})();
