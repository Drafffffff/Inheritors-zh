from pathlib import Path
import json
p=Path(__file__).resolve().parents[1];b=next((p/'original').glob('*')).read_bytes();out=[]
for i in range(27):
 for field,at,n in [('enemy',35,32),('technique',67,32),('equipment',99,32),('description',131,128)]:
  off=0x26ff4+i*260+at;t=b[off:off+n].split(b'\0')[0].decode('ascii')
  out.append(dict(offset=hex(off),en=t,field=field,max_bytes=n-1))
(p/'analysis/data_strings.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print('\n'.join(f"{i}: {r['field']} {r['en']}" for i,r in enumerate(out)))
