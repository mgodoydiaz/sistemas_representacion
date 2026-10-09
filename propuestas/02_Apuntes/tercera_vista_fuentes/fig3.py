import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
K="black"; B="#2E5E8C"; G="#A8A8A8"; TH=2.0; TN=0.8
C30,S30=np.cos(np.pi/6),0.5
def setup(w,h,xl,yl):
    f,a=plt.subplots(figsize=(w,h)); a.set_aspect("equal"); a.axis("off"); a.set_xlim(*xl); a.set_ylim(*yl); return f,a
def L(a,p,lw=TH,c=K,ls="-",z=3): a.plot([q[0] for q in p],[q[1] for q in p],color=c,lw=lw,ls=ls,zorder=z,solid_capstyle="round")
def poly(a,p,**k): L(a,list(p)+[p[0]],**k)
def T(a,x,y,s,fs=8,c=B,ha="center",va="center",**k): a.text(x,y,s,fs=fs,color=c,ha=ha,va=va,**k) if False else a.text(x,y,s,fontsize=fs,color=c,ha=ha,va=va,**k)
def num(a,x,y,n):
    a.add_patch(plt.Circle((x,y),4.5,color=B,zorder=6)); a.text(x,y,str(n),color="white",fontsize=9,ha="center",va="center",zorder=7,fontweight="bold")
# geometria: X ancho 60, Y fondo 40 (0 atras), Z alto 40
ALZ=[(0,0),(60,0),(60,20),(30,20),(30,40),(0,40)]
def alzado(a,c=K,lw=TH):
    poly(a,ALZ,c=c,lw=lw); L(a,[(0,20),(30,20)],c=c,lw=lw)
def planta(a,c=K,lw=TH,oy=-20):
    P=lambda x,y:(x,oy-y)
    poly(a,[P(0,0),P(60,0),P(60,40),P(0,40)],c=c,lw=lw); L(a,[P(30,0),P(30,25)],c=c,lw=lw); L(a,[P(0,25),P(30,25)],c=c,lw=lw)
LAT=[(0,0),(40,0),(40,20),(25,20),(25,40),(0,40)]
def lateral(a,c=K,lw=TH,ox=80,upto=None):
    poly(a,[(ox+u,v) for u,v in LAT],c=c,lw=lw)
def iso(x,y,z): return ((x-y)*C30, z-(x+y)*S30)
def box(a,x0,x1,y0,y1,z0,z1,ox=0,oy=0,s=1.0):
    def P(*p):
        u,v=iso(*p); return (ox+s*u,oy+s*v)
    faces=[[P(x0,y0,z1),P(x1,y0,z1),P(x1,y1,z1),P(x0,y1,z1)],[P(x0,y1,z0),P(x1,y1,z0),P(x1,y1,z1),P(x0,y1,z1)],[P(x1,y0,z0),P(x1,y1,z0),P(x1,y1,z1),P(x1,y0,z1)]]
    for f in faces: a.add_patch(Polygon(f,closed=True,fc="white",ec=K,lw=1.6,zorder=4,joinstyle="round"))
def pieza_iso(a,ox,oy,s=1.0):
    box(a,0,60,0,40,0,20,ox,oy,s); box(a,0,30,0,25,20,40,ox,oy,s)

# ---- Fig 1: correspondencias
f,a=setup(6.6,5.0,(-28,150),(-84,58))
alzado(a); planta(a); lateral(a)
pieza_iso(a,108,-44,0.5)
for x in (0,30,60): L(a,[(x,0),(x,-20)],lw=TN,c=B,ls=(0,(4,3)))
for z in (0,20,40): L(a,[(60 if z<=20 else 30,z),(80,z)],lw=TN,c=B,ls=(0,(4,3)))
T(a,30,47,"Alzado",c=K,fs=9,style="italic"); T(a,100,47,"Lateral izquierda",c=K,fs=9,style="italic"); T(a,30,-68,"Planta",c=K,fs=9,style="italic")
T(a,-14,-10,"mismo\nancho",fs=8); T(a,70,-10+38,"",fs=8)
T(a,70,48,"misma\naltura",fs=8)
a.annotate("",xy=(-6,-60),xytext=(-6,-20),arrowprops=dict(arrowstyle="<->",color=B,lw=1)); T(a,-17,-40,"fondo\n40",fs=8)
a.annotate("",xy=(120,-8),xytext=(80,-8),arrowprops=dict(arrowstyle="<->",color=B,lw=1)); T(a,100,-14,"fondo 40",fs=8)
T(a,112,-78,"Pieza de ejemplo",fs=8)
f.savefig("t3_01_correspondencia.png",dpi=300,bbox_inches="tight",pad_inches=0.05); plt.close(f)

# ---- Fig 2: 4 pasos
f,axs=plt.subplots(2,2,figsize=(7.4,7.0))
tit=["Ubicar la vista y trazar la recta a 45°","Llevar las alturas desde el alzado","Llevar los fondos desde la planta","Unir, decidir visibles y ocultas"]
for i,a in enumerate(axs.flat):
    a.set_aspect("equal"); a.axis("off"); a.set_xlim(-12,132); a.set_ylim(-72,60)
    alzado(a,c=G,lw=1.4); planta(a,c=G,lw=1.4)
    num(a,-4,53,i+1); a.text(4,53,tit[i],fontsize=8.5,color=B,va="center",ha="left",fontweight="bold")
    # recta 45
    L(a,[(70,-10),(126,-66)],lw=TN,c=B if i==0 else G)
    if i==0:
        L(a,[(80,-6),(80,46)],lw=TN,c=B,ls=(0,(4,3))); T(a,112,-40,"45°",fs=8)
        T(a,106,20,"aquí va la\nlateral\nizquierda",fs=8)
    if i>=1:
        for z in (0,20,40): L(a,[(60 if z<=20 else 30,z),(124,z)],lw=TN,c=B if i==1 else G,ls=(0,(4,3)))
    if i>=2:
        for y in (0,25,40):
            c=B if i==2 else G
            L(a,[(60 if y!=25 else 30,-20-y),(80+y,-20-y),(80+y,44)],lw=TN,c=c,ls=(0,(4,3)))
            if i==2: a.plot([80+y],[-20-y],"o",ms=3.5,color=B,zorder=6)
    if i==3: lateral(a)
    if i==2:
        for u in (0,25,40):
            for v in (0,20,40): a.plot([80+u],[v],"o",ms=2.5,color=B,zorder=6)
f.subplots_adjust(wspace=0.02,hspace=0.02)
f.savefig("t3_02_pasos.png",dpi=300,bbox_inches="tight",pad_inches=0.05); plt.close(f)

# ---- Fig 3: dos vistas no bastan
f,a=setup(7.2,2.9,(-8,262),(-70,56))
poly(a,[(0,0),(60,0),(60,40),(0,40)]); L(a,[(0,15),(60,15)])
poly(a,[(0,-20),(60,-20),(60,-60),(0,-60)]); L(a,[(0,-35),(60,-35)])
T(a,30,48,"Alzado y planta dados",c=K,fs=8.5,style="italic")
opts=[("A: escalón",[(0,0),(40,0),(40,15),(15,15),(15,40),(0,40)],None),("B: plano inclinado",[(0,0),(40,0),(40,15),(15,40),(0,40)],None),("C: superficie curva",None,"arc")]
for k,(name,pts,kind) in enumerate(opts):
    ox=90+k*60
    if pts: poly(a,[(ox+u,v) for u,v in pts])
    else:
        t=np.linspace(np.pi,1.5*np.pi,60); arc=[(ox+40+25*np.cos(tt),40+25*np.sin(tt)) for tt in t]
        L(a,[(ox+15,40),(ox,40),(ox,0),(ox+40,0),(ox+40,15)]); L(a,arc)
    T(a,ox+20,-10,name,fs=8)
T(a,170,48,"Tres laterales posibles",c=K,fs=8.5,style="italic")
T(a,170,-30,"Las tres piezas tienen el mismo alzado y la misma planta.\nSolo la tercera vista dice cuál es.",fs=8)
f.savefig("t3_03_ambiguedad.png",dpi=300,bbox_inches="tight",pad_inches=0.05); plt.close(f)
