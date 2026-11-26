const DATA = {
  "words": [
    {
      "hanzi": "我",
      "pinyin": "wǒ",
      "english": "I",
      "chapter": 1
    },
    {
      "hanzi": "你",
      "pinyin": "nǐ",
      "english": "you",
      "chapter": 1
    },
    {
      "hanzi": "在",
      "pinyin": "zài",
      "english": "at",
      "chapter": 1
    },
    {
      "hanzi": "图书馆",
      "pinyin": "túshūguǎn",
      "english": "library",
      "chapter": 1
    },
    {
      "hanzi": "看",
      "pinyin": "kàn",
      "english": "to read or look at",
      "chapter": 1
    },
    {
      "hanzi": "书",
      "pinyin": "shū",
      "english": "book",
      "chapter": 1
    },
    {
      "hanzi": "喜欢",
      "pinyin": "xǐhuan",
      "english": "to like",
      "chapter": 2
    },
    {
      "hanzi": "喝",
      "pinyin": "hē",
      "english": "to drink",
      "chapter": 2
    },
    {
      "hanzi": "茶",
      "pinyin": "chá",
      "english": "tea",
      "chapter": 2
    },
    {
      "hanzi": "也",
      "pinyin": "yě",
      "english": "also",
      "chapter": 2
    },
    {
      "hanzi": "吗",
      "pinyin": "ma",
      "english": "yes-or-no question particle",
      "chapter": 2
    }
  ],
  "foundation": [],
  "sentences": [
    {
      "id": "sample-1",
      "hanzi": "我在图书馆看书。",
      "tokens": [
        "我",
        "在",
        "图书馆",
        "看",
        "书",
        "。"
      ],
      "pinyin": "Wǒ zài túshūguǎn kàn shū.",
      "english": "I read at the library.",
      "chapter": 1,
      "minimumChapter": 1,
      "grammarIds": [
        "location"
      ],
      "family": "original",
      "generated": false
    },
    {
      "id": "sample-2",
      "hanzi": "你在图书馆看书。",
      "tokens": [
        "你",
        "在",
        "图书馆",
        "看",
        "书",
        "。"
      ],
      "pinyin": "Nǐ zài túshūguǎn kàn shū.",
      "english": "You read at the library.",
      "chapter": 1,
      "minimumChapter": 1,
      "grammarIds": [
        "location"
      ],
      "family": "original",
      "generated": false
    },
    {
      "id": "sample-3",
      "hanzi": "你看书，我看书。",
      "tokens": [
        "你",
        "看",
        "书",
        "，",
        "我",
        "看",
        "书",
        "。"
      ],
      "pinyin": "Nǐ kàn shū, wǒ kàn shū.",
      "english": "You read, and I read.",
      "chapter": 1,
      "minimumChapter": 1,
      "grammarIds": [],
      "family": "original",
      "generated": false
    },
    {
      "id": "sample-4",
      "hanzi": "你喜欢喝茶吗？",
      "tokens": [
        "你",
        "喜欢",
        "喝",
        "茶",
        "吗",
        "？"
      ],
      "pinyin": "Nǐ xǐhuan hē chá ma?",
      "english": "Do you like drinking tea?",
      "chapter": 2,
      "minimumChapter": 2,
      "grammarIds": [
        "question"
      ],
      "family": "original",
      "generated": false
    },
    {
      "id": "sample-5",
      "hanzi": "你在图书馆喝茶吗？",
      "tokens": [
        "你",
        "在",
        "图书馆",
        "喝",
        "茶",
        "吗",
        "？"
      ],
      "pinyin": "Nǐ zài túshūguǎn hē chá ma?",
      "english": "Do you drink tea at the library?",
      "chapter": 2,
      "minimumChapter": 2,
      "grammarIds": [
        "location",
        "question"
      ],
      "family": "original",
      "generated": false
    },
    {
      "id": "sample-6",
      "hanzi": "我喜欢看书，也喜欢喝茶。",
      "tokens": [
        "我",
        "喜欢",
        "看",
        "书",
        "，",
        "也",
        "喜欢",
        "喝",
        "茶",
        "。"
      ],
      "pinyin": "Wǒ xǐhuan kàn shū, yě xǐhuan hē chá.",
      "english": "I like reading, and I also like drinking tea.",
      "chapter": 2,
      "minimumChapter": 2,
      "grammarIds": [
        "also"
      ],
      "family": "original",
      "generated": false
    }
  ],
  "grammar": [
    {
      "id": "location",
      "chapter": 1,
      "form": "在 + place + action",
      "explanation": "Put the location before the action to say where it happens."
    },
    {
      "id": "question",
      "chapter": 2,
      "form": "Statement + 吗?",
      "explanation": "Add 吗 to the end of a statement to turn it into a yes-or-no question."
    },
    {
      "id": "also",
      "chapter": 2,
      "form": "也 + verb",
      "explanation": "Put 也 before the verb to add another action or preference."
    }
  ]
};
