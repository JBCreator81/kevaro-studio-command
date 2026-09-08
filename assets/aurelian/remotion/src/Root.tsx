import {Composition, Folder} from 'remotion';
import {AurelianFilm} from './AurelianFilm';
export const AurelianRoot = () => <Folder name="Aurelian-Symphony-of-Serenity">
  <Composition id="AurelianVertical" component={AurelianFilm} durationInFrames={720} fps={24} width={1080} height={1920} defaultProps={{format:'vertical' as const}}/>
  <Composition id="AurelianMaster" component={AurelianFilm} durationInFrames={720} fps={24} width={3840} height={2160} defaultProps={{format:'landscape' as const}}/>
</Folder>;
