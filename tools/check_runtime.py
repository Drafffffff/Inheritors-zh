from pathlib import Path
import ctypes as C,json,hashlib,struct
from PIL import Image
P=Path(__file__).resolve().parents[1];ROOT=P.parent;O=P/'analysis/runtime';O.mkdir(exist_ok=True)
c=C.CDLL(str(P/'build/runtime_bridge.dylib'))
c.anguna_open.argtypes=[C.c_char_p];c.anguna_open.restype=C.c_int;c.anguna_pixels.restype=C.c_void_p;c.anguna_read.argtypes=[C.c_uint,C.c_uint];c.anguna_read.restype=C.c_uint;c.anguna_write.argtypes=[C.c_uint]*3;c.anguna_call.argtypes=[C.c_uint]*4;c.anguna_call.restype=C.c_int
rom=P/'output/inheritors_zh.gba';assert c.anguna_open(str(rom).encode())
def run(n,k=0):c.anguna_frame(k,n)
def press(k,n=90):run(1,k);run(n)
def shot(n):
 im=Image.frombytes('RGB',(240,160),C.string_at(c.anguna_pixels(),240*160*2),'raw','BGR;16',0);im.save(O/(n+'.png'));im.resize((720,480),Image.Resampling.NEAREST).save(O/(n+'_3x.png'))
run(1000);shot('boot');press(8);shot('title');press(1);press(1);press(1,300);shot('game');press(64,180);shot('dialog1')
for i in range(2,7):press(1,120);shot('dialog'+str(i))
press(1,120);press(8);shot('inventory');press(1);shot('equipment');press(1);shot('equipment_detail');press(2);press(2);press(8);press(16);press(16);press(16);press(16);shot('config_selected');press(1);shot('config')
# RAM-only battle fixture enters the original battle routine with one level-1 foe.
press(2);press(32);press(1);shot('save_empty');press(1);shot('save_written')
sram=bytes(c.anguna_read(0x0e000000+i,1) for i in range(256));assert sram[:4]==b'IotO' and sram[9]==1
press(2);press(2)
c.anguna_jump(0x08004e98,0,0,0);run(240);shot('battle_attack');press(16);shot('battle_technique_selected');press(1);shot('battle_technique');press(2);press(32);press(1);shot('battle_target');press(1,240);shot('battle_turn')
for i in range(12):press(1,120);shot('battle_progress_'+str(i))
shot('battle_result')
info=json.loads((P/'build/build.json').read_text());rs=json.loads((P/'analysis/coverage.json').read_text());data=rom.read_bytes();maxins=0
# Isolated RAM-only font fixture: validate rendered width, every CJK glyph,
# and that the renderer stays inside the dedicated 256x128 object text atlas.
for i in range(0,0x4000,4):c.anguna_write(0x06014000+i,0,4)
for i,rec in enumerate(rs):
 if rec['zh']==rec['en']:continue
 if rec['refs'][0]=='inline':addr=0x08000000+int(rec['offset'],16)
 else:addr=struct.unpack_from('<I',data,int(rec['refs'][0],16))[0]
 n=c.anguna_call(0x08006090,addr,0,0);assert n>=0
 expected=sum(8 if ord(ch)>127 else data[0x1bbac+ord(ch)-32] for ch in rec['zh'])
 assert c.anguna_result()==expected,(rec,c.anguna_result(),expected)
 n=c.anguna_call(0x080060c0,0,(i%14)*8,addr);assert n>=0;maxins=max(maxins,n)
 if i%14==13:
  for j in range(0,0x4000,4):c.anguna_write(0x06014000+j,0,4)
# Pixel-exact native 8px/12px glyph proofs, using the same shipped renderer.
chars=sorted(set(''.join(v['zh'] for v in rs))-set(chr(i) for i in range(128)))
import importlib.util
sp=importlib.util.spec_from_file_location('fontutil',ROOT/'ANGUNA/tools/build_zh.py');fu=importlib.util.module_from_spec(sp);sp.loader.exec_module(fu)
c.anguna_call5.argtypes=[C.c_uint]*6;c.anguna_call5.restype=C.c_int
for size,baseline in [(8,7),(12,10)]:
 font=fu.font_bitmaps(ROOT/f'ANGUNA/assets/fonts/fusion-pixel-{size}px-monospaced-zh_hans.bdf',size,baseline)
 for i,ch in enumerate(chars):
  for n in range(0,0x800,4):c.anguna_write(0x06014000+n,0,4)
  n=c.anguna_call5(int(info['symbols']['glyph'],16),0,0,128+i,size,0);assert n>=0
  pixels=font[ch]
  for y in range(size):
   for x in range(size):
    off=(x//8)*32+(y//8)*1024+(y%8)*4+x%8//2
    actual=(c.anguna_read(0x06014000+off,1)>>(x%2*4))&15
    expect=15 if pixels[y][x] else 10 if (x>0 and pixels[y][x-1]) or (y>0 and pixels[y-1][x]) else 0
    assert actual==expect,(ch,size,x,y,actual,expect)
# Every dialogue/tutorial fits four 12px rows; all 27 descriptions fit 3 rows.
for rec in rs:
 off=int(rec['offset'],16)
 if (0xa15308<=off<0xa167d4 or rec.get('field')=='description'):
  limits=[168,168,184,184] if 'field'not in rec else [157]*3
  widths=[12 if ord(ch)>127 else data[0x1bbac+ord(ch)-32] for ch in rec['zh']]
  line=0;w=0
  for width in widths:
   if w+width>limits[line]:line+=1;w=0
   assert line<len(limits),(rec,'truncated')
   w+=width
report=dict(sha256=hashlib.sha256(data).hexdigest(),records=len(rs),font_widths_checked=True,glyph_pixel_checks=len(chars)*2,dialogue_layout_checked=True,save_ui_written=True,battle_fixture='original force_fixed_encounter(0), attack and spirit-technique menus; RAM-only fixture',max_draw_instructions=maxins,limits='mGBA smoke test plus RAM-only renderer checks; not a complete playthrough or hardware test.')
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report));c.anguna_close()
