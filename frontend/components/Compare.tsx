'use client';
import {useState} from 'react';
export default function Compare({before,after,title}:{before:string;after:string;title:string}) {
  const [position,setPosition] = useState(50);
  return <div className="compare-wrap"><div className="compare-image" data-testid="before-after"><img src={after} alt={'Studio version of '+title}/><div className="compare-original" style={{clipPath:`inset(0 ${100-position}% 0 0)`}}><img src={before} alt={'Original photo of '+title}/></div><span className="image-label before-label">01 / ORIGINAL</span><span className="image-label after-label">02 / DEVELOPED</span><div className="compare-handle" style={{left:position+'%'}}><span>↔</span></div><input type="range" min="0" max="100" value={position} onChange={event=>setPosition(Number(event.target.value))} aria-label="Before and after comparison" aria-valuetext={`${position}% original photo, ${100-position}% studio photo`}/></div><p className="caption">Slide to compare. Arrow keys work, too. Product details always need your review.</p></div>;
}
