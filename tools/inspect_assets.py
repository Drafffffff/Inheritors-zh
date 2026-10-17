from pathlib import Path
from PIL import Image
import struct
p=Path(__file__).resolve().parents[1];d=p/'upstream/data';o=p/'analysis'
def pal(n):
 v=struct.unpack('<'+'H'*((d/n).stat().st_size//2),(d/n).read_bytes());return [tuple((c>>s&31)*255//31 for s in [0,5,10]) for c in v]
def tile(name,pname,w,h):
 b=(d/name).read_bytes();cols=pal(pname);im=Image.new('RGB',(w,h));px=im.load()
 for y in range(h):
  for x in range(w):
   off=(y//8*w//8+x//8)*32+(y%8)*4+x%8//2
   if off<len(b):px[x,y]=cols[(b[off]>>(4*(x%2)))&15]
 im.resize((w*3,h*3),Image.Resampling.NEAREST).save(o/(name+'.png'))
# object sheet 256px by64, 2D layout
for name,pname in [('btl_titlemenugfx.bin','btl_titlemenupal.bin'),('btl_titleobjgfx.bin','btl_titleobjpal.bin'),('btl_uimap.bin','btl_objpal.bin'),('btl_objmap.bin','btl_objpal.bin')]:
 tile(name,pname,256,(d/name).stat().st_size//128)
