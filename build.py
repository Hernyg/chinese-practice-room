from pathlib import Path
import json,re,shutil,zipfile,hashlib
from generate_patterns import generate, GRAMMAR_WORDS
from writing_vocab import load_writing_lessons
ROOT=Path(__file__).parent
out=ROOT/'dist';out.mkdir(exist_ok=True)
words=[]
for f in sorted((ROOT/'chapters').glob('chapter-*.md')):
 chapter=int(f.stem.split('-')[1]);text=f.read_text(encoding='utf-8')
 section=re.split(r'(?im)^## ',text)
 for sec in section:
  if not re.match(r'(?i)(new words|vocabulary)',sec):continue
  for line in sec.splitlines():
   if not line.startswith('|'):continue
   cells=[c.strip().replace('**','').replace('*','') for c in line.strip('|').split('|')]
   if not cells:continue
   offset=1 if (re.match(r'^\d+',cells[0]) or cells[0] in ['—','–','-']) else 0
   if len(cells)<offset+3:continue
   h,py,en=cells[offset:offset+3]
   if not re.search('[\u4e00-\u9fff]',h) or re.search('[A-Za-z]',h):continue
   h=re.sub(r'[（(].*?[）)]','',h).strip()
   if not any(w['hanzi']==h for w in words):words.append(dict(hanzi=h,pinyin=py,english=en,chapter=chapter))
foundation=json.loads((ROOT/'foundation.json').read_text(encoding='utf-8'))
# Prefer textbook entries where a foundation spelling overlaps them.
lookup={w['hanzi']:w for w in foundation + words}
# The HSK 1 source includes alternate readings and some surname spellings.
# Use the readings and word spacing for these meanings in the practice bank.
foundation_pinyin = {
 '看':'kàn', '几':'jǐ', '读':'dú', '听':'tīng', '上':'shàng', '吗':'ma',
 '个':'gè', '都':'dōu', '冷':'lěng', '那':'nà', '年':'nián', '三':'sān', '书':'shū',
 '北京':'Běijīng', '中国':'Zhōngguó', '汉语':'Hànyǔ', '电影':'diànyǐng', '电视':'diànshì',
 '爸爸':'bàba', '妈妈':'māma', '杯子':'bēizi', '桌子':'zhuōzi', '东西':'dōngxi',
 '儿子':'érzi', '女儿':'nǚ’ér', '朋友':'péngyou', '老师':'lǎoshī', '学生':'xuésheng',
 '同学':'tóngxué', '学校':'xuéxiào', '商店':'shāngdiàn', '医院':'yīyuàn', '工作':'gōngzuò',
 '学习':'xuéxí', '喜欢':'xǐhuan', '漂亮':'piàoliang', '衣服':'yīfu', '苹果':'píngguǒ',
 '怎么':'zěnme', '时候':'shíhou', '天气':'tiānqì', '我们':'wǒmen', '今天':'jīntiān',
 '明天':'míngtiān', '上午':'shàngwǔ', '下午':'xiàwǔ', '中午':'zhōngwǔ', '下雨':'xiàyǔ',
 '打电话':'dǎ diànhuà',
}
for word in foundation:
 word['pinyin']=foundation_pinyin.get(word['hanzi'],word['pinyin'])
# Productive pronoun plural: HSK1 我/你/他/她 + 们, already taught as 我们.
for h,py,en in [('你们','nǐmen','you (plural)'),('他们','tāmen','they'),('她们','tāmen','they (female)')]:
 lookup[h]=dict(hanzi=h,pinyin=py,english=en,chapter=0);foundation.append(lookup[h])
# Component of the HSK1 expression 打电话.
lookup['电话']=dict(hanzi='电话',pinyin='diànhuà',english='telephone; phone call',chapter=0);foundation.append(lookup['电话'])
grammar=json.loads((ROOT/'grammar_catalog.json').read_text(encoding='utf-8'))
for word in GRAMMAR_WORDS:
 if word['hanzi'] not in lookup:
  lookup[word['hanzi']]=word;foundation.append(word)
grammar_lookup={g['id']:g for g in grammar}

segment_keys=sorted(lookup,key=len,reverse=True)

def segment(token):
 if token in lookup or not re.search('[\u4e00-\u9fff]',token):return [token]
 keys=segment_keys
 def solve(pos):
  if pos==len(token):return []
  for k in keys:
   if token.startswith(k,pos):
    tail=solve(pos+len(k))
    if tail is not None:return [k]+tail
  return None
 return solve(0) or [token]
sentences=[];errors=[]
for f in sorted((ROOT/'chapters').glob('*.sentences.json')):
 for i,s in enumerate(json.loads(f.read_text(encoding='utf-8-sig'))):
  s['hanzi']=s['hanzi'].replace('王老师','老师')
  s['pinyin']=s['pinyin'].replace('Wáng lǎoshī','Lǎoshī').replace('Wáng Lǎoshī','Lǎoshī')
  s['english']=s['english'].replace('Teacher Wang','The teacher').replace('Mr. Wang','The teacher')
  s['tokens']=[x for t in s['tokens'] for x in segment(t.replace('王老师','老师'))]
  missing=[t for t in s['tokens'] if re.search('[\u4e00-\u9fff]',t) and t not in lookup]
  if missing:errors.append(dict(file=f.name,index=i,unknown=missing));continue
  minimum=max([s['chapter']]+[lookup[t]['chapter'] for t in s['tokens'] if t in lookup])
  text=''.join(s['tokens']);clean=lambda t:re.sub(r'[^\u4e00-\u9fff0-9]','',t)
  assert clean(text)==clean(s['hanzi']),(f,i,'token mismatch')
  # Reinsert punctuation exactly as authored rather than dropping it.
  tokens=[];pos=0
  for t in s['tokens']:
   idx=s['hanzi'].find(t,pos)
   if idx>pos:tokens.append(s['hanzi'][pos:idx])
   tokens.append(t);pos=idx+len(t)
  if pos<len(s['hanzi']):tokens.append(s['hanzi'][pos:])
  sentences.append(dict(s,id=f'{f.stem}-{i}',tokens=tokens,minimumChapter=minimum))
# Some earlier originals use later grammar with vocabulary already in scope.
original_grammar = {
 '这件衣服还可以，就买这件吧。': ['c05-hai', 'c05-jiu'],
 '运动对身体很好。': ['c10-dui'],
 '公共汽车真快！': ['c03-zhen'],
 '我的衣服是粉的。': ['c03-de'],
 '那个杯子是红的。': ['c03-de'],
 '左边的杯子是红色的。': ['c03-de'],
 '我看一下今天的报纸。': ['c03-yixia'],
 '这个房间是粉色的。': ['c03-de'],
 '我十一岁的时候开始学习汉语。': ['c04-shihou'],
 '他已经工作两年了。': ['c04-yijing'],
 '这件衣服有点儿大，我不买。': ['c05-youdianr'],
 '因为下雨，所以我没去游泳。': ['c06-because'],
 '我家离学校不远。': ['c07-li'],
 '机场离我家很远。': ['c07-li'],
 '我走十分钟就到学校。': ['c07-jiu'],
 '我今天下午再看电影。': ['c08-zai'],
 '他没有时间，明天再告诉我。': ['c08-zai'],
 '我想让她看看这件白衣服。': ['c08-pivotal', 'c08-redup'],
 '她喜欢白的，不喜欢黑的。': ['c03-de'],
 '她从七点开始上班。': ['c09-cong'],
 '我听懂这个问题了。': ['c09-result'],
 '我看完了。': ['c09-result'],
 '你做完了吗？': ['c09-result'],
 '多听汉语对学习很有帮助。': ['c10-dui'],
 '别在家里看手机。': ['c10-imperative'],
 '上课的时候，你别看手机。': ['c04-shihou', 'c10-imperative'],
 '今天的苹果比昨天便宜一些。': ['c11-bi'],
 '男老师比女老师大两岁。': ['c11-bi'],
 '你可能不认识我。': ['c11-keneng'],
 '我妻子穿得很漂亮。': ['c12-degree'],
 '弟弟穿得比我多。': ['c12-degree', 'c12-bi'],
 '电视开着呢。': ['c07-ne', 'c13-zhe'],
 '我手里拿着铅笔。': ['c13-zhe'],
 '电视开着，桌子上有书和水。': ['c13-zhe'],
 '他一直往学校走。': ['c13-wang'],
 '虽然天晴，但是天气很冷。': ['c14-although'],
 '我去过中国三次，还想再去玩儿。': ['c14-guo', 'c14-frequency', 'c08-zai'],
 '她看过这个电影两次，还觉得很有意思。': ['c14-guo', 'c14-frequency'],
 '虽然我去过几次，但是还想再去玩儿。': ['c14-although', 'c14-guo', 'c14-frequency'],
 '今天是十二月二十日，新年就要到了。': ['c15-soon'],
 '今天阴，明天要下雨了。': ['c15-soon'],
 '这个字写错了。': ['c09-result'],
 '今天是我上班的第一天。': ['c09-ordinal'],
}
for sentence in sentences:
 ids=original_grammar.get(sentence['hanzi'],[])
 sentence.update(grammarIds=ids,family='original',generated=False)
 sentence['minimumChapter']=max([sentence['minimumChapter']]+[grammar_lookup[g]['chapter'] for g in ids])
originals=sentences;sentences=[]
for i,s in enumerate(generate(lookup,grammar,segment)):
 s=dict(s);s['tokens']=[x for t in s['tokens'] for x in segment(t)]
 missing=[t for t in s['tokens'] if re.search('[\u4e00-\u9fff]',t) and t not in lookup]
 if missing:errors.append(dict(file='generated',index=i,unknown=missing,hanzi=s['hanzi']));continue
 assert ''.join(s['tokens'])==s['hanzi'],('generated token mismatch',s)
 assert s.get('grammarIds'),('missing grammar provenance',s)
 grammar_min=max(grammar_lookup[g]['chapter'] for g in s['grammarIds'])
 s['minimumChapter']=max([grammar_min,s['chapter']]+[lookup[t]['chapter'] for t in s['tokens'] if t in lookup])
 s['generated']=True;sentences.append(s)
sentences.extend(originals)
unique={}
for s in sentences:
 key=re.sub(r'[\s，。！？、,.!?]','',s['hanzi'])
 previous=unique.get(key)
 if previous is None or s['minimumChapter']<previous['minimumChapter']:
  unique[key]=s
 elif not s['generated'] and s['minimumChapter']==previous['minimumChapter']:
  s['grammarIds']=list(dict.fromkeys(previous['grammarIds']+s['grammarIds']))
  unique[key]=s
sentences=list(unique.values())
for key,s in unique.items():s['id']='s-'+hashlib.sha256(key.encode('utf-8')).hexdigest()[:20]
data=dict(words=words,foundation=foundation,sentences=sentences,grammar=grammar)
(out/'data.js').write_text('const DATA = '+json.dumps(data,ensure_ascii=False)+';',encoding='utf-8')
writing_lessons = load_writing_lessons(ROOT/'chapters')
(out/'writing-data.js').write_text(
 'const WRITING_LESSONS = '+json.dumps(writing_lessons,ensure_ascii=False)+';',encoding='utf-8')
writing_assets = {
 out/'strokes'/f'{ord(character):x}.{extension}'
 for lesson in writing_lessons for word in lesson['words'] for character in word['hanzi']
 for extension in ('gif','png')
}
reading_strokes = {
 out/'strokes'/f'{ord(character):x}.gif'
 for sentence in sentences for character in re.findall(r'[\u4e00-\u9fff]', sentence['hanzi'])
}
missing_strokes = {asset for asset in reading_strokes if not asset.is_file()}
if missing_strokes:
 raise FileNotFoundError(f'{len(missing_strokes)} Reading GIFs missing. Run generate_strokes.py with the pinned Hanzi Writer Data archive, then rebuild.')
(out/'chapters').mkdir(exist_ok=True)
with zipfile.ZipFile(out/'chapters.zip','w',zipfile.ZIP_DEFLATED)as z:
 for f in sorted((ROOT/'chapters').glob('*.md')):shutil.copy2(f,out/'chapters'/f.name);z.write(f,f.name)
shutil.copy2(ROOT/'FOUNDATION-LICENSE.txt',out/'FOUNDATION-LICENSE.txt')
shutil.copy2(ROOT/'GRAMMAR_PATTERNS.md',out/'GRAMMAR_PATTERNS.md')
with zipfile.ZipFile(out/'reading-room-offline.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ['index.html','style.css','app.js','data.js','chapters.zip','FOUNDATION-LICENSE.txt','GRAMMAR_PATTERNS.md',
              'reading-room-square.png','writing.html','writing.css','writing.js','writing-data.js','strokes/LICENSE.txt']:
  if name in ('index.html','writing.html'):
   html=(out/name).read_text(encoding='utf-8').replace('href="./?v=', 'href="index.html?v=')
   z.writestr(name,html)
  else:z.write(out/name,name)
 for f in (out/'chapters').glob('*.md'):z.write(f,'chapters/'+f.name)
 for f in sorted(writing_assets | reading_strokes):z.write(f,f.relative_to(out).as_posix())
 z.writestr('START HERE.txt','Open index.html in your browser. Everything needed for practice is included. The app works without an internet connection.\n')
report=dict(chapters=len(list((ROOT/'chapters').glob('*.md'))),words=len(words),sentences=len(sentences),excluded=errors,grammarCoverage={g['id']:sum(g['id'] in s.get('grammarIds',[]) for s in sentences) for g in grammar},newPerChapter={n:sum(s['minimumChapter']==n for s in sentences) for n in range(1,16)},pools={n:sum(s['minimumChapter']<=n for s in sentences) for n in range(1,16)})
(ROOT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True))
