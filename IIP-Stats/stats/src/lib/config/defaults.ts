import type { FormMetadata } from '$lib/types/forms/Form';
import type { ActorMetadata } from '$lib/types/actors/Actor';
import type { SegmentMetadata } from '$lib/types/segments/Segment';
import { SEGMENTS } from './segments';

export const DEFAULT_QUESTION: SegmentMetadata = 
  SEGMENTS.find(segment => segment.name === "Reto o área de oportunidad") 
  ?? SEGMENTS[0];


export const DEFAULT_INDEX: FormMetadata = {
	id: '68aa4a4f-0ce2-45d3-bde9-3f8a42055715',
	anno: '2023',
	name: 'Índice por defecto',
	description: 'Este es un índice por defecto usado como fallback.'
};

export const DEFAULT_ENTITY: ActorMetadata = {
	id: '1b01632f-f169-46c5-be3a-d1c1eee6f58c',
	name: 'Entidad por defecto',
	description: 'Este es una entidad por defecto usado como fallback.',
  mission: 'Esta es la misión por defecto',
  vision: 'Esta es la visión por defecto'
};
