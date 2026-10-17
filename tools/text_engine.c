typedef unsigned char u8;typedef unsigned short u16;typedef unsigned u32;
#include "zh_data.h"
static unsigned next(const u8 **p){unsigned c=*(*p)++;if(c>=128){unsigned lo=*(*p)++;return 128+(c-128)*254+lo-1;}return c;}
static unsigned advance(unsigned c,unsigned size){return c>=128?size:ORIG_FONT[c>=32?c-32:0];}
static void pixel(unsigned x,unsigned y,unsigned v){if(x>=256||y>=128)return;volatile u16 *a=(volatile u16 *)(0x06014000+(x>>3)*32+(y>>3)*1024+(y&7)*4+((x&7)>>2)*2);unsigned sh=(x&3)*4;*a=(*a&~(15<<sh))|(v<<sh);}
static void glyph(unsigned x,unsigned y,unsigned c,unsigned size){
 if(c>=128){unsigned id=c-128;if(id>=GLYPH_COUNT)return;const u16 *g=size==12?zh12[id]:zh8[id];
  for(unsigned yy=0;yy<size;yy++)for(unsigned xx=0;xx<size;xx++)if(g[yy]&(1<<xx)){pixel(x+xx,y+yy,15);if(xx+1<size&&!(g[yy]&(2<<xx)))pixel(x+xx+1,y+yy,10);if(yy+1<size&&!(g[yy+1]&(1<<xx)))pixel(x+xx,y+yy+1,10);}
 }else if(c>=32&&c<128){unsigned i=c-32,w=ORIG_FONT[i],pos=((const u16 *)(ORIG_FONT+96))[i];for(unsigned yy=0;yy<8;yy++)for(unsigned xx=0;xx<w;xx++){unsigned v=ORIG_FONT[288+yy*485+pos+xx];if(v)pixel(x+xx,y+yy,v);}}
}
__attribute__((used)) unsigned zh_width(const u8*p){unsigned w=0;while(*p)w+=advance(next(&p),8);return w;}
__attribute__((used)) void zh_draw(unsigned x,unsigned y,const u8*p){while(*p){unsigned c=next(&p);glyph(x,y,c,8);x+=advance(c,8);if(x>=256)break;}}
__attribute__((used)) void zh_wrap(int right,int y,const int*limits,int spacing,const u8*p){
 unsigned line=0,maxlines=spacing==8?4:3,size=12;spacing=spacing==8?12:14;
 while(*p&&line<maxlines){unsigned w=0;const u8 *start=p,*end=p,*space=0;unsigned lim=limits[line];
  while(*p){const u8 *prev=p;unsigned c=next(&p),a=advance(c,size);if(c=='\n'){end=prev;break;}if(w+a>lim){p=prev;break;}w+=a;end=p;if(c==32)space=prev;}
  if(end==start)break;
  // CJK can break between characters; Latin words prefer their last space.
  if(*p&&space&&space>start&&*p<128&&p[-1]<128){end=space;p=space+1;}
  unsigned x=right-lim;const u8*q=start;while(q<end){unsigned c=next(&q);glyph(x,y,c,size);x+=advance(c,size);}
  while(*p==32||*p=='\n')p++;line++;y+=spacing;
 }
}
