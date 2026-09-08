import {Audio} from '@remotion/media';
import {AbsoluteFill,Easing,Img,Sequence,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {AtmosphereScene} from './scenes/AtmosphereScene';
import {SymphonyScene} from './scenes/SymphonyScene';
import {HeroScene} from './scenes/HeroScene';
import {ProgressionScene} from './scenes/ProgressionScene';
import {EndFrameScene} from './scenes/EndFrameScene';
export type FilmFormat='vertical'|'landscape';
const Background=({format}:{format:FilmFormat})=>{const frame=useCurrentFrame();const {width,height}=useVideoConfig();const vertical=format==='vertical';return <AbsoluteFill style={{backgroundColor:'#071616',overflow:'hidden'}}>
  <Img src={staticFile('retreat-dawn-interior-v1.png')} style={{width,height,objectFit:'cover',opacity:interpolate(frame,[0,120,260,410],[.6,.78,.32,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),scale:interpolate(frame,[0,719],[1.08,1.18]),filter:'saturate(.72) contrast(1.06) brightness(.72)'}}/>
  <Img src={staticFile('retreat-blue-hour-pavilion-v1.png')} style={{position:'absolute',inset:0,width,height,objectFit:'cover',objectPosition:vertical?'58% center':'center',opacity:interpolate(frame,[220,410,650,719],[0,.28,.56,.28],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),scale:interpolate(frame,[220,719],[1.16,1.05],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),filter:'saturate(.65) contrast(1.08) brightness(.68)'}}/>
  <AbsoluteFill style={{background:'linear-gradient(145deg,rgba(4,17,17,.42),rgba(8,31,29,.12) 45%,rgba(185,151,91,.14))'}}/>
  <AbsoluteFill style={{background:vertical?'linear-gradient(180deg,rgba(2,10,10,.48),transparent 34%,transparent 67%,rgba(2,10,10,.72))':'linear-gradient(90deg,rgba(2,10,10,.55),transparent 38%,transparent 68%,rgba(2,10,10,.48))'}}/>
</AbsoluteFill>};
const FilmGrain=()=>{const frame=useCurrentFrame();return <AbsoluteFill style={{opacity:.07,backgroundImage:'radial-gradient(circle at '+((frame*17)%100)+'% '+((frame*29)%100)+'%,#fff 0 .7px,transparent .9px)',backgroundSize:'9px 9px',mixBlendMode:'soft-light'}}/>};
export const AurelianFilm=({format}:{format:FilmFormat})=>{const frame=useCurrentFrame();const {fps}=useVideoConfig();return <AbsoluteFill style={{fontFamily:'Aurelian Noto,sans-serif',color:'#f4eee0',opacity:interpolate(frame,[0,20,690,719],[0,1,1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(.16,1,.3,1)})}}>
  <style>{'@font-face{font-family:"Aurelian Noto";src:url("'+staticFile('NotoSans-wdth-wght.ttf')+'") format("truetype");font-style:normal;font-weight:100 900;font-display:block;}'}</style>
  <Background format={format}/>
  <Sequence from={0} durationInFrames={120} name="Atmospheric opening"><AtmosphereScene format={format}/></Sequence>
  <Sequence from={120} durationInFrames={168} name="Symphony visual language"><SymphonyScene format={format}/></Sequence>
  <Sequence from={288} durationInFrames={216} name="Renewal Serum hero"><HeroScene format={format}/></Sequence>
  <Sequence from={504} durationInFrames={144} name="Abstract progression"><ProgressionScene format={format}/></Sequence>
  <Sequence from={648} durationInFrames={72} name="End frame"><EndFrameScene format={format}/></Sequence>
  <FilmGrain/>
  <Audio src={staticFile('symphony-of-serenity-score-v1.wav')} volume={(f)=>interpolate(f,[0,fps,27*fps,30*fps],[0,1,1,.72],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}/>
  <Audio src={staticFile('symphony-of-serenity-sfx-v1.wav')} volume={(f)=>interpolate(f,[0,2*fps,28*fps,30*fps],[0,.9,.9,.5],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}/>
</AbsoluteFill>};
