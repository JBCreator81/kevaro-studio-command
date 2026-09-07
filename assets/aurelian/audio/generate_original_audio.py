"""Deterministically generate Aurelian production-specific original audio.

Uses only Python's standard library and mathematical synthesis. No samples,
recordings, external libraries, or third-party musical works are used.
"""
from __future__ import annotations
import math, random, struct, wave
from pathlib import Path

RATE=48_000
DURATION=30
FRAMES=RATE*DURATION
OUT=Path(__file__).parent

def envelope(t: float) -> float:
    return min(1.0,t/2.0,(DURATION-t)/2.5)

def write(name: str, sample):
    with wave.open(str(OUT/name),'wb') as wav:
        wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(RATE)
        block=bytearray()
        for i in range(FRAMES):
            value=max(-1.0,min(1.0,sample(i/RATE,i)))
            packed=struct.pack('<h',int(value*32767))
            block.extend(packed); block.extend(packed)
            if len(block)>=RATE*4:
                wav.writeframesraw(block); block.clear()
        if block: wav.writeframesraw(block)

def score(t: float, _: int) -> float:
    # Original sparse pentatonic-like harmonic bed; no sampled or quoted melody.
    roots=(110.0,146.832,164.814,130.813)
    root=roots[min(3,int(t//7.5))]
    shimmer=0.5+0.5*math.sin(2*math.pi*0.07*t)
    tones=sum(math.sin(2*math.pi*root*r*t+p)*a for r,p,a in ((1,0,.20),(1.5,.7,.09),(2,1.1,.055),(3,2.0,.025)))
    bell=sum(math.sin(2*math.pi*(root*mult)*(t-hit))*math.exp(-2.2*(t-hit)) for hit,mult in ((3.0,4),(10.5,3),(18.0,4.5),(25.0,3)) if t>=hit)
    return envelope(t)*(tones*(0.55+0.18*shimmer)+0.055*bell)

rng=random.Random(20260907)
noise=[rng.uniform(-1,1) for _ in range(FRAMES)]
def sfx(t: float, i: int) -> float:
    # Deterministic synthesized water/air texture and soft transition accents.
    n=(noise[i]+(noise[i-1] if i else 0)+(noise[i-2] if i>1 else 0))/3
    water=.055*n*(.5+.5*math.sin(2*math.pi*.19*t))
    air=.018*math.sin(2*math.pi*(55+3*math.sin(2*math.pi*.05*t))*t)
    accents=0.0
    for hit in (7.4,14.9,22.4,28.2):
        d=t-hit
        if 0<=d<1.5: accents+=.06*math.sin(2*math.pi*(180-70*d)*d)*math.exp(-3*d)
    return envelope(t)*(water+air+accents)

if __name__=='__main__':
    write('symphony-of-serenity-score-v1.wav',score)
    write('symphony-of-serenity-sfx-v1.wav',sfx)
