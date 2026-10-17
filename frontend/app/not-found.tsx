import Link from 'next/link';
export default function NotFound(){return <div className="page empty-state"><p className="eyebrow">FRAME NOT FOUND / 404</p><h1>This shelf is empty.</h1><p>That page isn’t in the catalog. Start a new listing instead.</p><Link className="button accent" href="/create">Open the studio ↗</Link></div>;}
