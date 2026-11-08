"""Make every sound from noise and small physical models. Loops carry extra samples at each end so that they can run with no gap."""
import numpy as np, os, subprocess
from scipy import signal as sg
from scipy.io import wavfile
ROOT=os.path.dirname(__file__)+'/..'; WAV=ROOT+'/audio/wav'; OUT=ROOT+'/web/assets/audio'; os.makedirs(WAV,exist_ok=True); os.makedirs(OUT,exist_ok=True)
SR=44100; rng=np.random.default_rng(7); PAD=int(.25*SR)
def bp(x,lo,hi,o=2): return sg.sosfilt(sg.butter(o,[lo,hi],'bp',fs=SR,output='sos'),x,axis=0)
def lp(x,f,o=2): return sg.sosfilt(sg.butter(o,f,'lp',fs=SR,output='sos'),x,axis=0)
def hp(x,f,o=2): return sg.sosfilt(sg.butter(o,f,'hp',fs=SR,output='sos'),x,axis=0)
def pink(n):
    w=rng.standard_normal(n+2048); f=np.fft.rfft(w); f/=np.maximum(np.arange(len(f)),1)**.5; return np.fft.irfft(f)[:n]
def drops(n,rate,fmin,fmax,dmin,dmax,gain=(0.3,1.),sparse=None):
    """Sound of drops hitting something: many small decaying resonances, with a wrap so the loop has no seam."""
    out=np.zeros(n); N=rng.poisson(rate*n/SR); t=rng.integers(0,n,N)
    if sparse is not None: t=t[rng.random(N)<sparse[t*len(sparse)//n]]
    L=int(.06*SR); tt=np.arange(L)/SR
    for k in range(0,len(t)):
        f=np.exp(rng.uniform(np.log(fmin),np.log(fmax))); d=rng.uniform(dmin,dmax); a=rng.uniform(*gain)**2
        e=np.exp(-tt/d)*np.sin(2*np.pi*f*tt*(1+.2*np.exp(-tt/.004)))*a
        i=t[k]; j=min(L,n-i); out[i:i+j]+=e[:j]; 
        if j<L: out[:L-j]+=e[j:]
    return out
# Long term spectra measured from the reference soundtrack, in dB per octave band centred on these frequencies. Only the shape is used.
CEN=np.array([85,170,350,700,1400,2800,5600,9500,16000.])
TARGET=dict(rain_forest=[-94,-76,-69,-65,-66,-73,-77,-82,-92],rain_tent=[-85,-72,-65,-62,-65,-71,-76,-82,-94],fire=[-81,-71,-65,-61,-64,-68,-67,-72,-86],sizzle=[-77,-71,-62,-59,-64,-68,-72,-78,-90],drips=[-85,-72,-65,-62,-65,-71,-76,-82,-94])
def match(x,name):
    '''Move the sound's average spectrum to the target shape with a smooth curve.'''
    if name not in TARGET: return x
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); P=np.abs(X)**2; have=[]
    for c in CEN:
        m=(f>c/1.414)&(f<c*1.414); have.append(10*np.log10(P[m].mean()+1e-20))
    d=np.array(TARGET[name])-np.array(have); d-=d.max(); g=10**(np.interp(np.log(f+1),np.log(CEN),d)/20); return np.fft.irfft(X*g,len(x))
def loop(name,L,left,right=None,gain=1.,q='112k'):
    """Crossfade the tail into the head, then add the padding."""
    if right is None: right=left
    left=match(left,name); right=match(right,name)
    X=np.stack([left,right],1); F=int(1.5*SR); head=X[:F].copy(); tail=X[-F:].copy(); k=np.linspace(0,1,F)[:,None]; Y=X[:-F].copy(); Y[:F]=tail*(1-k)**.5+head*k**.5; 
    Y=Y/np.max(np.abs(Y))*.9*gain; full=np.vstack([Y[-PAD:],Y,Y[:PAD]])
    w=f'{WAV}/{name}.wav'; wavfile.write(w,SR,(full*32000).astype('i2'))
    subprocess.run(['ffmpeg','-v','error','-y','-i',w,'-c:a','aac','-b:a',q,f'{OUT}/{name}.m4a'],check=True); return len(Y)/SR
def oneshot(name,x,gain=.9,q='96k'):
    if x.ndim==1: x=np.stack([x,x],1)
    fade=np.ones(len(x)); nf=min(800,len(x)//4); fade[-nf:]=np.linspace(1,0,nf); x=x*fade[:,None]; x=x/np.max(np.abs(x))*gain; w=f'{WAV}/{name}.wav'; wavfile.write(w,SR,(x*32000).astype('i2'))
    subprocess.run(['ffmpeg','-v','error','-y','-i',w,'-c:a','aac','-b:a',q,f'{OUT}/{name}.m4a'],check=True)
D=42; n=D*SR; lens={}
slow=lambda s,a=.4: 1+a*np.interp(np.arange(n),np.linspace(0,n,int(D/s)+2),rng.uniform(-1,1,int(D/s)+2))
# rain in the forest: broad hiss from far, a bed of leaf ticks, heavier drops close by
def forest(s):
    bed=hp(lp(pink(n),9000),300)*.34*slow(5)
    far=bp(pink(n),250,1400)*.3*slow(9)
    tick=drops(n,900,1800,7500,.002,.008,(.15,.8))*.22
    fat=drops(n,70,300,1500,.006,.02,(.3,1.))*.5
    return bed+far+tick+fat
lens['rain_forest']=loop('rain_forest',D,forest(0),forest(1),.8)
# rain on a tight tent skin close above the head: a broad drum of thuds and bright patters
def fabric(s):
    pat=drops(n,1500,500,3400,.003,.012,(.2,1.))*.46; thud=drops(n,220,120,420,.012,.03,(.35,1.))*.65; hiss=hp(lp(pink(n),5200),500)*.1*slow(6); drum=lp(pink(n),260)*.34*slow(4)
    return pat+thud+hiss+drum
lens['rain_tent']=loop('rain_tent',D,fabric(0),fabric(1),.85)
# big slow drips from the pines onto cloth
def dr(s):
    env=np.ones(n); return drops(n,5,350,1100,.015,.05,(.5,1.))*1.2+drops(n,2.2,180,420,.02,.05,(.6,1.))
lens['drips']=loop('drips',D,dr(0),dr(1),.7)
# wind in the crowns
w0=bp(pink(n),180,1100)*slow(7,.7)**2; w1=bp(pink(n),180,1100)*slow(7,.7)**2; lens['wind']=loop('wind',D,w0,w1,.8)
# fire: low breath, crackles
def fire(s):
    r=lp(pink(n),320)*.8*slow(1.6,.45); h=bp(pink(n),500,2600)*.1*slow(.7,.7); c=drops(n,12,900,5200,.0012,.006,(.3,1.))*1.1+drops(n,2.5,300,900,.003,.012,(.4,1.))*1.3
    return r+h+c
lens['fire']=loop('fire',D,fire(0),fire(1),.8)
# sizzle: dense bursts of bright noise that swell and settle
def siz(s):
    a=hp(lp(rng.standard_normal(n),11000),2300)*.3*slow(1.2,.6)**2; b=drops(n,230,2300,8000,.0008,.004,(.3,1.))*.7; return a+b
lens['sizzle']=loop('sizzle',24,siz(0),siz(1),.75) if False else loop('sizzle',D,siz(0),siz(1),.75)
# birds after the rain: short sweeps, little families, far away
def birds(s):
    out=np.zeros(n); t=0
    while t<D-3:
        kind=rng.integers(4); base=rng.uniform(1900,5200); notes=rng.integers(3,9); pos=int(t*SR); pan=rng.uniform(.25,1)
        for i in range(notes):
            L=int(rng.uniform(.05,.16)*SR); tt=np.arange(L)/SR; sw=rng.uniform(-1,1)*700; f=base*(1+.06*i if kind==0 else 1+.18*np.sin(i*1.8) if kind==1 else 1)+sw*tt/tt[-1]; ph=2*np.pi*np.cumsum(f)/SR+1.5*np.sin(2*np.pi*rng.uniform(30,70)*tt); e=np.hanning(L)**1.5
            if pos+L<n: out[pos:pos+L]+=np.sin(ph)*e*(.25+.75*pan)
            pos+=L+int(rng.uniform(.02,.14)*SR)
        t+=rng.exponential(2.2)+.5
    w=lp(out,7000); ir=np.exp(-np.arange(int(.5*SR))/SR/.13)*rng.standard_normal(int(.5*SR)); return w*.5+sg.fftconvolve(w,ir,'same')*.06
lens['birds']=loop('birds',D,birds(0),birds(1),.7)
# grinder burrs
g=bp(rng.standard_normal(n//3),700,4200)*(1+.55*np.sin(2*np.pi*3.2*np.arange(n//3)/SR))*drops(n//3,0,1,2,.1,.2,(1,1)).__add__(1); lens['grind']=loop('grind',D/3,g,g,.7)
# one shots
def t(s): return np.arange(int(s*SR))/SR
def env(tt,a,d): return np.minimum(tt/a,1)*np.exp(-tt/d)
oneshot('pump_up',bp(rng.standard_normal(len(t(1.4))),300,1800)*np.sin(np.pi*t(1.4)/1.4)**2*.5)
x=t(1.8); oneshot('pump_down',bp(rng.standard_normal(len(x)),160,1200)*np.sin(np.pi*x/1.8)**1.5+.5*np.sin(2*np.pi*72*x)*env(x,.05,.3))
x=t(.9); oneshot('match',hp(rng.standard_normal(len(x)),1500)*env(x,.02,.13)+bp(rng.standard_normal(len(x)),300,2500)*env(x,.1,.5)*.4)
x=t(.25); oneshot('chop',.8*np.sin(2*np.pi*230*x)*env(x,.002,.03)+bp(rng.standard_normal(len(x)),800,5000)*env(x,.001,.02)*.6+.4*np.sin(2*np.pi*640*x)*env(x,.001,.012))
x=t(4.5); fl=np.linspace(600,2400,len(x)); pr=sum(np.sin(2*np.pi*np.cumsum(fl*k)/SR)*.2/k for k in (1,1.5,2.3)); oneshot('pour',(bp(rng.standard_normal(len(x)),400,5000)*.7+pr*.5)*(1+.3*np.sin(2*np.pi*13*x))*np.minimum(x/.2,1)*np.minimum((4.5-x)/.6,1))
x=t(1.2); oneshot('sip',bp(rng.standard_normal(len(x)),900,5200)*env(x,.2,.3))
x=t(.3); oneshot('tap',sum(np.sin(2*np.pi*f*x)*np.exp(-x/.09)*a for f,a in ((980,.6),(2300,.3),(3700,.12))))
x=t(5.); oneshot('chime',sum(a*np.sin(2*np.pi*f*x)*np.exp(-x/d) for f,a,d in ((528,.5,1.6),(1057,.28,1.1),(1584,.14,.7),(2640,.05,.35)))*np.minimum(x/.004,1),.5)
x=t(.9); oneshot('pant',sum((bp(rng.standard_normal(len(x)),700,3200)*np.maximum(np.sin(2*np.pi*3.4*x+p),0)**2)for p in (0,)))
x=t(.5); oneshot('thump',lp(rng.standard_normal(len(x)),260)*env(x,.004,.05))
for i in range(4):
    x=t(.32); oneshot(f'step{i}',hp(lp(rng.standard_normal(len(x)),1900+i*300),120)*env(x,.012,.05)+drops(len(x),80,1500,5000,.001,.004,(.2,.8))*.5)
for i,dur in enumerate((14,19)):
    m=int(dur*SR); x=np.arange(m)/SR; ro=lp(pink(m),90+i*30)*(np.minimum(x/1.2,1)*np.exp(-x/(4.5+i*1.2)))*(1+.5*np.sin(2*np.pi*.7*x+i)*np.sin(2*np.pi*.23*x)); r2=lp(pink(m),220)*np.exp(-((x-1.5-i)/1.1)**2)*.5
    oneshot(f'thunder{i}',ro+r2,.8,'80k')
import json; json.dump({k:dict(start=PAD/SR,end=PAD/SR+v) for k,v in lens.items()},open(OUT+'/loops.json','w')); print(lens)
