from pathlib import Path
import json,struct,hashlib
P=Path(__file__).resolve().parents[1];rom=(P/'output/inheritors_zh.gba').read_bytes();rs=json.loads((P/'analysis/coverage.json').read_text());checks=[]
def width(s,size=8):return sum(size if ord(c)>127 else rom[0x1bbac+ord(c)-32] for c in s)
for rec in rs:
 off=int(rec['offset'],16);s=rec['zh'];size=8;limits=[128];kind='compact static label'
 if rec['en']==s:kind='explicit retention';limits=[1024]
 elif 0xa15308<=off<0xa167d4:kind='dialogue/message';size=12;limits=[168,168,184,184]
 elif rec.get('field')=='description' or 0xa16a5c<=off<0xa16b08:kind='technique/accessory description';size=12;limits=[157]*3
 elif 0xa16814<=off<0xa16a24:kind='ending/credits line';limits=[224]
 elif rec.get('field'):kind='name';limits=[128]
 line=0;w=0;rows=[]
 for ch in s:
  a=width(ch,size)
  if w+a>limits[line]:rows.append(w);line+=1;w=0
  assert line<len(limits),(rec,'overflow')
  w+=a
 rows.append(w)
 assert 'max_bytes' not in rec or len(bytes.fromhex(rec['encoded']))<=rec['max_bytes']
 checks.append(dict(offset=rec['offset'],kind=kind,size=size,row_widths=rows,limits=limits,encoded_bytes=len(bytes.fromhex(rec['encoded']))))
# Two-column attribute bounds from all 27 shipped crystals, four legal slots.
original=(P/'original/Inheritors-of-the-Oubliette-v1.2.gba').read_bytes();attrs=[struct.unpack_from('<6h',original,0x26ff4+i*260+4) for i in range(27)]
bases=[100,60,30,35,30,25];prefixes=['生命:','真气:','力量:','防御:','敏捷:','灵力:'];dynamic=[]
for a,prefix in enumerate(prefixes):
 maxadd=max(row[a]//2 for row in attrs);maxval=bases[a]+maxadd*4
 for add in sorted({row[a]//2 for row in attrs}):
  s=prefix+str(maxval)+(f'(+{add})' if add else '')
  w=width(s);assert w<=80,(s,w)
  dynamic.append(dict(text=s,width=w,cell_width=80,buffer_bytes=sum(2 if ord(c)>127 else 1 for c in s)+1,buffer_capacity=48))
# Worst numerical save preview uses both characters at four-slot HP/MP bounds.
for a,prefix in [(0,'生命:'),(1,'真气:')]:
 value=bases[a]+4*max(row[a]//2 for row in attrs);s=prefix+f'{value}/{value}  {value}/{value}  '
 assert width(s)<=157 and sum(2 if ord(c)>127 else 1 for c in s)+1<=48,(s,width(s))
 dynamic.append(dict(text=s,width=width(s),cell_width=157,buffer_capacity=48))
out=dict(sha256=hashlib.sha256(rom).hexdigest(),records_checked=len(checks),translated=sum(x['zh']!=x['en'] for x in rs),retained=sum(x['zh']==x['en'] for x in rs),layout_checks=checks,dynamic_composites=dynamic,limits='Data-derived four-slot stat bounds; not arbitrary corrupted saves or every possible game state.')
(P/'analysis/qa_layout.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('pass',len(checks),'records',len(dynamic),'dynamic composites; max attribute width',max(x['width'] for x in dynamic if x['cell_width']==80))
