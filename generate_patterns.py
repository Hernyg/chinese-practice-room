"""Bilingual HSK 2 templates with curated, interchangeable phrase slots."""
from itertools import product
import re
from string import Formatter

GRAMMAR_WORDS = [
    {"hanzi": hanzi, "pinyin": pinyin, "english": english, "chapter": chapter}
    for hanzi, pinyin, english, chapter in [
        ("第", "dì", "ordinal prefix", 9),
        # Verb heads reused in the chapter 12 degree-complement construction.
        ("跑", "pǎo", "run", 12),
        ("游", "yóu", "swim", 12),
        ("唱", "chàng", "sing", 12),
        ("跳", "tiào", "dance; jump", 12),
    ]
]

PEOPLE = [
    ("他", "he", "him", "his"), ("她", "she", "her", "her"),
    ("老师", "the teacher", "the teacher", "the teacher's"),
    ("妈妈", "Mom", "Mom", "Mom's"), ("爸爸", "Dad", "Dad", "Dad's"),
    ("我朋友", "my friend", "my friend", "my friend's"),
    ("我同学", "my classmate", "my classmate", "my classmate's"),
    ("他儿子", "his son", "his son", "his son's"),
    ("她女儿", "her daughter", "her daughter", "her daughter's"),
    ("那个学生", "that student", "that student", "that student's"),
]
# Action glosses supply each English inflection explicitly.
ACTIONS = [
    ("看 电影", "watch a movie", "watches a movie", "watched a movie", "watching a movie"),
    ("听 汉语", "listen to Chinese", "listens to Chinese", "listened to Chinese", "listening to Chinese"),
    ("读 书", "read a book", "reads a book", "read a book", "reading a book"),
    ("喝 茶", "drink tea", "drinks tea", "drunk tea", "drinking tea"),
    ("写 字", "write", "writes", "written", "writing"),
    ("学习", "study", "studies", "studied", "studying"),
    ("踢足球", "play soccer", "plays soccer", "played soccer", "playing soccer"),
    ("运动", "exercise", "exercises", "exercised", "exercising"),
    ("打电话", "make a phone call", "makes a phone call", "made a phone call", "making a phone call"),
]
PLACES = [("学校", "school"), ("医院", "the hospital"), ("商店", "the store"),
          ("饭店", "the restaurant"), ("北京", "Beijing"), ("中国", "China")]
LOCAL_PLACES = PLACES[:4] + [("公司", "the office"), ("机场", "the airport")]
TIMES = [("今天", "today"), ("明天", "tomorrow"), ("今天 下午", "this afternoon"),
         ("明天 上午", "tomorrow morning"), ("明天 中午", "tomorrow at noon")]
HOURS = [(hanzi + " 点", f"{number} o’clock") for number, hanzi in
         enumerate("一二三四五六七八九十", 1)]
OBJECTS = [("书", "book", "本", "books"), ("杯子", "cup", "个", "cups"),
           ("苹果", "apple", "个", "apples"), ("电脑", "computer", "台", "computers"),
           ("衣服", "piece of clothing", "件", "pieces of clothing")]
NUMBERS = list(zip("一两三四五六七八九十", ["one", "two", "three", "four", "five",
                                           "six", "seven", "eight", "nine", "ten"]))


def generate(lookup, grammar_catalog, segment):
    """Render each recipe and resolve its Chinese into chapter-indexed tokens."""
    chapters = {point["id"]: point["chapter"] for point in grammar_catalog}
    sentences = []

    class Phrase(tuple):
        def __str__(self):
            return self[0]

    def add(pattern, chinese, english, **slots):
        fields = {field.split("[")[0] for _, field, _, _ in Formatter().parse(chinese) if field}
        assert fields == slots.keys(), (pattern, fields, slots.keys())
        for values in product(*slots.values()):
            zh = chinese.format(**{key: Phrase(value) for key, value in zip(slots, values)})
            tokens = [token for piece in re.findall(r"[^\s，。！？、]+|[，。！？、]", zh)
                      for token in segment(piece)]
            words = [token for token in tokens if token not in "，。！？、"]
            if any(token not in lookup for token in words):
                continue
            en = english.format(**{key: value[1:] for key, value in zip(slots, values)})
            en = re.sub(r"(^|[.!?] +)([a-z])", lambda match: match[1] + match[2].upper(), en)
            pinyin = " ".join(lookup[token]["pinyin"] if token in lookup else token for token in tokens)
            pinyin = re.sub(r" ([，。！？])", r"\1", pinyin).strip()
            pinyin = pinyin.translate(str.maketrans("，。！？", ",.!?"))
            if pattern in {"c14-guo", "c14-frequency"}:
                pinyin = pinyin.replace(" guò ", " guo ")
            pinyin = pinyin[0].upper() + pinyin[1:]
            sentences.append(dict(
                hanzi="".join(tokens), pinyin=pinyin, english=en, tokens=tokens,
                chapter=chapters[pattern], grammarIds=[pattern], family=chinese,
            ))

    add("c01-yao", "{s} {t} 要 {a}。", "{s[0]} plans to {a[0]} {t[0]}.", s=PEOPLE, t=TIMES, a=ACTIONS)
    add("c01-zui", "{s} 最 喜欢 {a}。", "{s[0]} likes {a[3]} best.", s=PEOPLE, a=ACTIONS)
    add("c01-approx", "{s} 有 几 {o[2]} {o[0]}。", "{s[0]} has a few {o[2]}.", s=PEOPLE, o=OBJECTS)
    add("c01-approx", "{s} 想 买 十 多 {o[2]} {o[0]}。", "{s[0]} wants to buy more than ten {o[2]}.", s=PEOPLE, o=OBJECTS[:3])

    add("c02-shibushi", "{s} {t} 是不是 要 {a}？", "Is {s[0]} planning to {a[0]} {t[0]}?", s=PEOPLE, t=TIMES, a=ACTIONS)
    add("c02-mei", "{s} 每 天 {h} 起床。", "{s[0]} gets up at {h[0]} every day.", s=PEOPLE, h=HOURS[4:9])
    add("c02-duo", "{s} 的 {r} 多 高？", "How tall is {s[2]} {r[0]}?", s=PEOPLE[:5],
        r=[("爸爸", "father"), ("妈妈", "mother"), ("儿子", "son"), ("女儿", "daughter")])

    add("c03-de", "这 {o[2]} {o[0]} 是 {s} 的。", "This {o[0]} belongs to {s[1]}.", s=PEOPLE,
        o=OBJECTS[:3])
    add("c03-yixia", "{s} {t} 要 看 一下 {o}。", "{s[0]} plans to take a quick look at {o[0]} {t[0]}.",
        s=PEOPLE, t=TIMES, o=[("报纸", "the newspaper"), ("那 本 书", "that book"), ("手表", "the watch")])
    add("c03-zhen", "{s} 的 {o} 真 {a}！", "{s[2]} {o[0]} is really {a[0]}!", s=PEOPLE,
        o=[("房间", "room"), ("手表", "watch"), ("新 衣服", "new clothing")],
        a=[("漂亮", "beautiful"), ("好", "nice")])

    add("c04-shide", "这 {o[2]} {o[0]} 是 {s} 买 的。", "It was {s[0]} who bought this {o[0]}.", s=PEOPLE, o=OBJECTS)
    add("c04-shihou", "{s} {n} 岁 的 时候 开始 {a}。", "{s[0]} started {a[3]} at age {n[0]}.", s=PEOPLE,
        n=NUMBERS[5:]+[("十一", "eleven"), ("十二", "twelve")], a=ACTIONS[6:8]+[("学习 汉语", "", "", "", "studying Chinese")])
    add("c04-yijing", "{s} 已经 在 {p} 工作 {n} 年 了。", "{s[0]} has already worked in {p[0]} for {n[0]} years.",
        s=PEOPLE, p=PLACES[-2:], n=NUMBERS[1:])

    add("c05-jiu", "这 {o[2]} {o[0]} 不错，{s} 就 买 这 {o[2]} 吧。", "This {o[0]} looks good. {s[0]} should get this one.",
        s=PEOPLE, o=OBJECTS)
    add("c05-hai", "{s} 的 {o} 还 不错。", "{s[2]} {o[0]} is pretty good.", s=PEOPLE,
        o=[("书", "book"), ("咖啡", "coffee"), ("手表", "watch"), ("房间", "room"), ("工作", "job")])
    add("c05-youdianr", "{s} 觉得 {o} 有点儿 {a}。", "{s[0]} thinks {o[0]} is a little {a[0]}.", s=PEOPLE,
        o=[("这 个 房间", "this room"), ("他 的 房间", "his room"), ("她 的 房间", "her room"), ("家 里", "home")],
        a=[("冷", "cold"), ("热", "hot"), ("小", "small")])

    add("c06-zenme", "{s} {t} 怎么 不 {a}？", "How come {s[0]} won’t {a[0]} {t[0]}?", s=PEOPLE, t=TIMES[1:], a=ACTIONS)
    add("c06-measure", "{o} 个个 都 {a}。", "Every one of {o[0]} {a[0]}.",
        o=[("我们 的 学生", "our students"), ("他们 的 学生", "their students"),
           ("她 的 孩子", "her children"), ("他 的 孩子", "his children")],
        a=[("喜欢 打篮球", "likes playing basketball"), ("喜欢 游泳", "likes swimming"), ("喜欢 运动", "likes exercising")])
    add("c06-because", "因为 {r}，所以 {s} 今天 不 {a}。", "Because {r[0]}, {s[0]} won’t {a[0]} today.",
        s=PEOPLE, r=[("下雨", "it’s raining"), ("天气 太 冷", "it’s too cold"), ("天气 太 热", "it’s too hot")],
        a=ACTIONS[6:8]+[("游泳", "go swimming"), ("打篮球", "play basketball")])

    add("c07-hai", "{s} 还 没 到 {p} 呢。", "{s[0]} hasn’t arrived at {p[0]} yet.", s=PEOPLE, p=LOCAL_PLACES)
    add("c07-jiu", "{s} {h} 就 到 {p} 了。", "{s[0]} got to {p[0]} as early as {h[0]}.", s=PEOPLE, h=HOURS[4:8], p=LOCAL_PLACES)
    add("c07-li", "{s} 家 离 {p} 很 {a}。", "{s[2]} home is {a[0]} {p[0]}.", s=PEOPLE, p=LOCAL_PLACES,
        a=[("远", "far from"), ("近", "close to")])
    add("c07-ne", "{s} 还 在 {a} 呢。", "{s[0]} is still {a[3]}.", s=PEOPLE, a=ACTIONS)

    add("c08-haoma", "我们 {t} 一起 {a}，好 吗？", "How about we {a[0]} together {t[0]}?", t=TIMES, a=ACTIONS)
    add("c08-zai", "{s} {t} 再 {a}。", "{s[0]} will {a[0]} again {t[0]}.", s=PEOPLE, t=TIMES, a=ACTIONS)
    add("c08-pivotal", "{s} 想 让 {r} {a}。", "{s[0]} wants {r[1]} to {a[0]}.", s=PEOPLE[:5], r=PEOPLE[5:], a=ACTIONS)
    add("c08-redup", "{s} 想 看看 {o}。", "{s[0]} would like to take a look at {o[0]}.", s=PEOPLE,
        o=[("那 件 衣服", "that piece of clothing"), ("这 本 书", "this book"), ("这 个 手表", "this watch")])

    add("c09-result", "{s} 看 完 {o} 了。", "{s[0]} has finished {o[0]}.", s=PEOPLE,
        o=[("那 本 书", "reading that book"), ("今天 的 报纸", "reading today’s newspaper"), ("这 个 电影", "watching this movie")])
    add("c09-cong", "{s} 从 {h} 开始 {a}。", "{s[0]} starts {a[3]} at {h[0]}.", s=PEOPLE, h=HOURS[4:], a=ACTIONS)
    add("c09-ordinal", "{s} 想 问 第 {n} 个 问题。", "{s[0]} wants to ask question number {n[0]}.",
        s=PEOPLE, n=[("一", "one"), ("二", "two")]+NUMBERS[2:])

    add("c10-imperative", "{s}，别 在 {p} {a} 了。", "{s[0]}, please don’t keep {a[3]} in {p[0]}.",
        s=[("妈妈", "Mom"), ("爸爸", "Dad"), ("哥哥", "Brother"), ("姐姐", "Sis"), ("老师", "Teacher")],
        p=[("教室", "the classroom"), ("房间 里", "the room"), ("家 里", "the house")],
        a=[("打电话", *ACTIONS[-1][1:]), ("看 电视", "", "", "", "watching TV"),
           ("吃 东西", "", "", "", "eating"), ("说话", "", "", "", "talking")])
    add("c10-dui", "{s} 觉得 {a} 对 {r} 的 身体 好。", "{s[0]} thinks {a[3]} is good for {r[2]} health.",
        s=PEOPLE[:5], r=PEOPLE[5:], a=ACTIONS[6:8]+[("跑步", "", "", "", "running"), ("游泳", "", "", "", "swimming"),
                                               ("打篮球", "", "", "", "playing basketball")])

    add("c11-attributive", "{s} {v} 的 {o} 在 {p}。", "The {o[0]} {s[0]} {v[0]} is {p[0]}.",
        s=PEOPLE, v=[("买", "bought"), ("送", "gave away")],
        o=[("书", "book"), ("手表", "watch"), ("衣服", "clothing")],
        p=[("桌子 上", "on the table"), ("房间 里", "in the room"), ("家 里", "at home")])
    add("c11-bi", "{s} 比 {r} {a}。", "{s[0]} is {a[0]} than {r[1]}.", s=PEOPLE[:5], r=PEOPLE[5:],
        a=[("高", "taller"), ("忙", "busier"), ("大", "older")])
    add("c11-keneng", "{s} {t} 可能 去 {p}。", "{s[0]} might go to {p[0]} {t[0]}.", s=PEOPLE, t=TIMES, p=PLACES)

    skills = [("跑步 跑", "runs"), ("游泳 游", "swims"), ("唱歌 唱", "sings"), ("跳舞 跳", "dances"),
              ("汉语 说", "speaks Chinese"), ("字 写", "writes characters")]
    add("c12-degree", "{s} {v} 得 {a}。", "{s[0]} {v[0]} {a[0]}.", s=PEOPLE, v=skills,
        a=[("很 好", "very well"), ("不 错", "quite well"), ("不 太 好", "less well than expected")])
    add("c12-bi", "{s} {v} 得 比 {r} 好。", "{s[0]} {v[0]} better than {r[1]}.", s=PEOPLE[:5], r=PEOPLE[5:], v=skills)

    add("c13-zhe", "{s} 手 里 拿 着 {n} {o[2]} {o[0]}。", "{s[0]} is holding {n[0]} {o[2]}.", s=PEOPLE,
        n=NUMBERS[1:5], o=[OBJECTS[0], OBJECTS[1], OBJECTS[2]])
    add("c13-rhetorical", "{s} 不是 {t} 要 {a} 吗？", "Isn’t {s[0]} planning to {a[0]} {t[0]}?", s=PEOPLE, t=TIMES, a=ACTIONS)
    add("c13-wang", "{s} 一直 往 {p} 走。", "{s[0]} keeps walking toward {p[0]}.", s=PEOPLE, p=LOCAL_PLACES)

    add("c14-guo", "{s} {v} 过 {o} 吗？", "Has {s[0]} ever {v[0]} {o[0]}?", s=PEOPLE,
        v=[("看", "watched")], o=[("这 个 电影", "this movie"), ("那 个 电影", "that movie")])
    add("c14-guo", "{s} 读 过 {o} 吗？", "Has {s[0]} ever read {o[0]}?", s=PEOPLE,
        o=[("这 本 书", "this book"), ("那 本 书", "that book")])
    add("c14-although", "虽然 {s} {t} 很 忙，但是 {a} 的 时间 还 是 有 的。", "Although {s[0]} is busy {t[0]}, there is still time to {a[0]}.",
        s=PEOPLE, t=TIMES, a=ACTIONS)
    add("c14-frequency", "{s} 去 过 {p} {n} 次。", "{s[0]} has been to {p[0]} {n[0]} times.", s=PEOPLE,
        p=[("北京", "Beijing"), ("中国", "China")], n=NUMBERS[1:])

    add("c15-soon", "{s} 就 要 去 {p} {a} 了。", "{s[0]} is about to go to {p[0]} to {a[0]}.", s=PEOPLE,
        p=[("北京", "Beijing"), ("中国", "China")],
        a=[("旅游", "travel"), ("工作", "work"), ("学习 汉语", "study Chinese")])
    add("c15-dou", "都 {h} 了，{s} 还 没 {a}。", "It’s already {h[0]}, and {s[0]} still hasn’t {a[2]}.",
        h=HOURS, s=PEOPLE, a=ACTIONS)

    return sentences
