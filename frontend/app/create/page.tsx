import {Suspense} from 'react';
import Studio from '@/components/Studio';
export default function Page(){return <Suspense fallback={<div className="page"><p className="eyebrow">OPENING THE DARKROOM…</p></div>}><Studio/></Suspense>;}
