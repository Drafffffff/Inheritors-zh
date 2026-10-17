from pathlib import Path
import json,sys,struct,hashlib,subprocess,importlib.util
P=Path(__file__).resolve().parents[1];ROOT=P.parent;B=P/'build';B.mkdir(exist_ok=True)
expected='1d8b4617be75a8b7b6c5c2975ef0213ed37da669c460d967d4259b6a25d22b2e';r=next((P/'original').glob('*.gba')).read_bytes();assert hashlib.sha256(r).hexdigest()==expected
spec=importlib.util.spec_from_file_location('fontutil',ROOT/'ANGUNA/tools/build_zh.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
runtime=P/'translations/runtime_zh.json'
rr=json.loads((runtime if runtime.exists() else P/'analysis/strings.json').read_text())
for v in rr:v.setdefault('zh',v['en'])
rs=rr+json.loads((P/'translations/data_zh.json').read_text())
chars=sorted(set(''.join(v['zh'] for v in rs))-set(chr(i) for i in range(128)));cid={c:i for i,c in enumerate(chars)}
def encode(s):
 b=bytearray()
 for c in s:
  if ord(c)<128:b.append(ord(c))
  else:i=cid[c];b.extend([128+i//254,1+i%254])
 return bytes(b)
h=['#define ORIG_FONT ((const u8*)0x0801bbac)',f'#define GLYPH_COUNT {len(chars)}']
for size,baseline in [(8,7),(12,10)]:
 fs=mod.font_bitmaps(ROOT/f'ANGUNA/assets/fonts/fusion-pixel-{size}px-monospaced-zh_hans.bdf',size,baseline)
 assert not set(chars)-fs.keys(),set(chars)-fs.keys()
 data=[[sum(v<<x for x,v in enumerate(row)) for row in fs[c]] for c in chars]
 h.append(f'static const u16 zh{size}[][{size}]={{'+','.join('{'+','.join(map(str,a))+'}' for a in data)+'};')
(B/'zh_data.h').write_text('\n'.join(h))
base=(len(r)+4095)&~4095
(B/'patch.ld').write_text(f'SECTIONS {{ . = 0x{0x08000000+base:x}; .patch : {{ *(.text*) *(.rodata*) }} /DISCARD/ : {{ *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) }} }}')
tool=ROOT/'POWDER/toolchain/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin'
subprocess.run([str(tool/'arm-none-eabi-gcc'),'-mcpu=arm7tdmi','-mthumb','-Os','-ffreestanding','-fno-builtin','-nostdlib','-I'+str(B),'-Wl,-T,'+str(B/'patch.ld'),'-o',str(B/'patch.elf'),str(P/'tools/text_engine.c')],check=True)
subprocess.run([str(tool/'arm-none-eabi-objcopy'),'-O','binary',str(B/'patch.elf'),str(B/'patch.bin')],check=True)
syms={a[2]:int(a[0],16) for l in subprocess.check_output([str(tool/'arm-none-eabi-nm'),str(B/'patch.elf')],text=True).splitlines() if len(a:=l.split())==3}
out=bytearray(r)+bytearray(b'\xff'*(base-len(r)))+(B/'patch.bin').read_bytes();report=[]
for v in rs:
 off=int(v['offset'],16);en=v['en'].encode('ascii');assert r[off:off+len(en)]==en,v
 zh=encode(v['zh'])
 if 'max_bytes'in v:
  assert len(zh)<=v['max_bytes'],v
  out[off:off+v['max_bytes']+1]=zh+b'\0'*(v['max_bytes']+1-len(zh));refs=['inline']
 elif v['zh']==v['en']:refs=['retained']
 else:
  at=0x08000000+len(out);out.extend(zh+b'\0');old=struct.pack('<I',0x08000000+off);p=0;refs=[]
  while(p:=r.find(old,p))>=0:
   # Only aligned compiler references; binary fields patched separately above.
   if p%4==0:out[p:p+4]=struct.pack('<I',at);refs.append(hex(p))
   p+=1
  assert refs,('No references',v)
 report.append(dict(v,encoded=zh.hex(),refs=refs))
for off,name,check in [(0x6090,'zh_width','03780200'),(0x60c0,'zh_draw','f0b5de46')]:
 assert r[off:off+4].hex()==check
 out[off:off+8]=struct.pack('<HHI',0x4b00,0x4718,syms[name]|1)
# Preserve the fourth argument (r3) and stack fifth argument.
off=0xa8f4;assert r[off:off+4].hex()=='f0b5de46'
out[off:off+16]=struct.pack('<6HI',0xb408,0x4b02,0x469c,0xbc08,0x4760,0x46c0,syms['zh_wrap']|1)
# Graphics patch is deterministic and independent of engine.
sys.path.insert(0,str(P/'tools'))
if (P/'tools/graphics_zh.py').exists():
 from graphics_zh import apply_graphics
 graphics=apply_graphics(out)
else:graphics={}
out[0xbd]=(-sum(out[0xa0:0xbd])-0x19)&255
(P/'output/inheritors_zh.gba').write_bytes(out)
info=dict(original_sha256=expected,sha256=hashlib.sha256(out).hexdigest(),bytes=len(out),translations=len(rs),glyphs=len(chars),symbols={k:hex(v) for k,v in syms.items()},graphics=graphics)
(B/'build.json').write_text(json.dumps(info,ensure_ascii=False,indent=2));(P/'analysis/coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(info,ensure_ascii=False,indent=2))
