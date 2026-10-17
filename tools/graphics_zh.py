from pathlib import Path
import struct,importlib.util
from PIL import Image
P=Path(__file__).resolve().parents[1];ROOT=P.parent
sp=importlib.util.spec_from_file_location('fu',ROOT/'ANGUNA/tools/build_zh.py');fu=importlib.util.module_from_spec(sp);sp.loader.exec_module(fu)
fonts={n:fu.font_bitmaps(ROOT/f'ANGUNA/assets/fonts/fusion-pixel-{n}px-monospaced-zh_hans.bdf',n,7 if n==8 else 10) for n in [8,12]}
def unpack(b,w=256):
 h=len(b)*2//w;pix=[[0]*w for _ in range(h)]
 for y in range(h):
  for x in range(w):
   at=(y//8*(w//8)+x//8)*32+(y%8)*4+x%8//2;pix[y][x]=(b[at]>>(x%2*4))&15
 return pix
def pack(p):
 h=len(p);w=len(p[0]);b=bytearray(w*h//2)
 for y in range(h):
  for x in range(w):
   at=(y//8*(w//8)+x//8)*32+(y%8)*4+x%8//2;b[at]|=p[y][x]<<(x%2*4)
 return b
def text(p,s,x,y,size=8,ink=15,shadow=10,scale=1):
 for c in s:
  rows=fonts[size][c];advance=size if ord(c)>127 else size//2
  for yy,row in enumerate(rows):
   for xx,v in enumerate(row):
    if v:
     for dy in range(scale):
      for dx in range(scale):
       xxx=x+xx*scale+dx;yyy=y+yy*scale+dy
       if 0<=yyy<len(p)-1 and 0<=xxx<len(p[0])-1:
        if p[yyy][xxx+1]!=ink:p[yyy][xxx+1]=shadow
        if p[yyy+1][xxx]!=ink:p[yyy+1][xxx]=shadow
        p[yyy][xxx]=ink
  x+=advance*scale

def apply_graphics(rom):
 report=[]
 def asset(name):
  d=(P/'upstream/data'/name).read_bytes();off=bytes(rom).find(d);assert off>=0,name;return off,d,unpack(d)
 def save(name,off,d,p,pal):
  b=pack(p);assert len(b)==len(d);rom[off:off+len(b)]=b
  colors=struct.unpack('<16H',(P/'upstream/data'/pal).read_bytes()[:32]);im=Image.new('RGB',(256,len(p)));im.putdata([tuple(((colors[v]>>s)&31)*255//31 for s in [0,5,10]) for row in p for v in row]);im.resize((768,len(p)*3),Image.Resampling.NEAREST).save(P/'analysis'/(name+'_zh.png'));report.append(name)
 name='btl_titlemenugfx.bin';off,d,p=asset(name)
 for i,s in enumerate(['开始游戏','读取存档','系统设置']):
  for left in [0,128]:
   for y in range(i*16,i*16+16):p[y][left:left+96]=[0]*96
   text(p,s,left+24,i*16+1,12,2,1 if left==0 else 4)
 save(name,off,d,p,'btl_titlemenupal.bin')
 name='btl_titleobjgfx.bin';off,d,p=asset(name)
 for y in range(56):p[y][:224]=[0]*224
 text(p,'遗落之境',64,2,12,2,6,2);text(p,'继承者',76,29,12,3,6,2)
 save(name,off,d,p,'btl_titleobjpal.bin')
 name='btl_uimap.bin';off,d,p=asset(name)
 # Configuration controls: preserve borders and each selected/unselected background.
 for y,s in [(192,'显示模式'),(208,'记忆光标'),(224,'操作方式'),(240,'LR平移')]:
  for x0 in ([0,128] if y==240 else [0,64]):
   bg=p[y+3][x0+3];fg=15 if x0==0 else 2;sh=10 if x0==0 else 15
   for yy in range(y+3,y+13):p[yy][x0+3:x0+61]=[bg]*58
   text(p,s,x0+(64-len(s)*8)//2,y+4,8,fg,sh)
 # Alternate L/R scheme, normal and highlighted.
 for x0 in [64,192]:
  y=240;bg=p[y+3][x0+3]
  for yy in range(y+3,y+13):p[yy][x0+3:x0+61]=[bg]*58
  text(p,'LR转向',x0+10,y+4,8,15 if x0==64 else 2,10 if x0==64 else 15)
 # Toggle labels fit their 32px button cell.
 for x0,s in [(128,'开'),(160,'关'),(192,'开'),(224,'关')]:
  y=208;bg=p[y+3][x0+3]
  for yy in range(y+3,y+13):p[yy][x0+3:x0+29]=[bg]*26
  text(p,s,x0+12,y+4,8,15 if x0<192 else 2,10 if x0<192 else 15)
 for yy in range(224,240):p[yy][128:256]=[0]*128
 text(p,'A:保存设置',128,224);text(p,'B:取消',128,232)
 save(name,off,d,p,'btl_objpal.bin')
 name='btl_objmap.bin';off,d,p=asset(name)
 # MISS occupies a dedicated 16x8 HUD cell; two 8px glyphs fit exactly.
 for yy in range(24,32):p[yy][112:128]=[0]*16
 text(p,'未中',112,24)
 save(name,off,d,p,'btl_objpal.bin')
 return report
