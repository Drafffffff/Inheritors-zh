"""Record consecutive native frames in the original and Chinese ROMs.
A RAM-only original battle entry is explicitly marked; no fixture enters ROM.
"""
from pathlib import Path
import ctypes as C,json,hashlib,struct,sys
from collections import Counter
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];D=P/'analysis/qa_review_frames';D.mkdir(exist_ok=True)
c=C.CDLL(str(P/'build/runtime_bridge.dylib'));c.anguna_open.argtypes=[C.c_char_p];c.anguna_open.restype=C.c_int;c.anguna_pixels.restype=C.c_void_p;c.anguna_read.argtypes=[C.c_uint,C.c_uint];c.anguna_read.restype=C.c_uint;c.anguna_jump.argtypes=[C.c_uint]*4
report=json.loads((D/"report.json").read_text()) if (D/"report.json").exists() else {}
for version,rom in [('original',P/'original/Inheritors-of-the-Oubliette-v1.2.gba'),('zh',P/'output/inheritors_zh.gba')]:
 if '--zh-only' in sys.argv and version!='zh':continue
 loaded_sha=hashlib.sha256(rom.read_bytes()).hexdigest()
 assert c.anguna_open(str(rom).encode());out=D/version;out.mkdir(exist_ok=True);steps=[]
 def run(n,k=0):c.anguna_frame(k,n)
 def press(k,n=90):run(1,k);run(n)
 def frame():return Image.frombytes('RGB',(240,160),C.string_at(c.anguna_pixels(),240*160*2),'raw','BGR;16',0)
 def trace(name,k=0,n=90,fixture=False):
  frames=[];stats=[];previous=None
  for i in range(n):
   run(1,k if i==0 else 0);im=frame();raw=im.tobytes();h=hashlib.sha256(raw).hexdigest();pixels=list(im.getdata());dark=sum(max(p)<8 for p in pixels)
   delta=sum(a!=b for a,b in zip(raw,previous))/len(raw) if previous else 0
   stats.append(dict(frame=i,sha256=h,black_fraction=dark/38400,changed_channel_fraction=delta))
   frames.append(im);previous=raw
  frames[-1].resize((720,480),Image.Resampling.NEAREST).save(out/(name+'_stable_3x.png'))
  frames[0].save(out/(name+'.gif'),save_all=True,append_images=frames[1:],duration=17,loop=0,optimize=False)
  selected=sorted(set([0,1,2,3,4,8,16,24,32,48,64,n-1])&set(range(n)))
  sheet=Image.new('RGB',(240*4,180*((len(selected)+3)//4)))
  for j,i in enumerate(selected):sheet.paste(frames[i],(j%4*240,j//4*180));ImageDraw.Draw(sheet).text((j%4*240,j//4*180+160),f'{name}: frame {i}',fill='white')
  sheet.save(out/(name+'_contact.png'));(out/(name+'_frames.json')).write_text(json.dumps(stats,indent=2))
  steps.append(dict(name=name,frames=n,fixture=fixture,nearly_black_frames=[x['frame'] for x in stats if x['black_fraction']>.98],unique_frames=len({x['sha256'] for x in stats}),max_changed_channel_fraction=max(x['changed_channel_fraction'] for x in stats),stable_sha256=stats[-1]['sha256']))
 run(1000);trace('title',8);press(1);press(1);trace('new_game_scene',1,180);trace('opening_dialog',64,180)
 for i in range(6):trace(f'dialog_{i+2}',1,90)
 trace('close_dialog',1);trace('open_menu',8);trace('equipment_menu',1);trace('equipment_detail',1);trace('equipment_back',2);trace('close_equipment_menu',2);trace('open_menu_again',8)
 for i in range(4):trace(f'menu_selection_{i}',16,45)
 trace('configuration',1);trace('configuration_back',2);trace('save_selection',32);trace('save_slots',1);trace('save_write',1);trace('save_back',2);trace('menu_exit',2)
 trace('turn_right',16,60);trace('move_forward',64,90)
 c.anguna_jump(0x08004e98,0,0,0);trace('battle_entry',0,240,True);trace('battle_technique_selected',16);trace('battle_technique_menu',1);trace('battle_technique_back',2);trace('battle_attack_selected',32);trace('battle_attack_target',1);trace('battle_attack_turn',1,240)
 for i in range(12):trace(f'battle_progress_{i}',1,90)
 report[version]=dict(rom_sha256=loaded_sha,steps=steps,total_frames=sum(x['frames'] for x in steps));c.anguna_close()
(D/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({v:{'total_frames':r['total_frames'],'steps':len(r['steps']),'black':[(s['name'],len(s['nearly_black_frames'])) for s in r['steps'] if s['nearly_black_frames']]} for v,r in report.items()}))
