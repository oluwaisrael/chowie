'use client';
import {useQuery} from '@tanstack/react-query';
import {api} from '@/lib/api';
import {Catalog,Item,money} from '@/lib/types';
import Link from 'next/link';
import {ArrowUpRight,ArrowRight} from 'lucide-react';
export const useCatalog=(initialData?:Catalog)=>useQuery({initialData,queryKey:['catalog'],queryFn:()=>api<Catalog>('/catalog')});
export function ErrorBox({message,retry}:{message:string;retry?:()=>void}){return <div className="error-box" role="alert"><p>{message}</p>{retry&&<button className="text-link" onClick={retry}>Try again</button>}</div>}
export function Loading(){return <div className="loading" role="status"><span className="spinner"/> Bringing things to the table…</div>}
export function Empty({title,description,href='/menu',action='Explore the menu'}:{title:string;description:string;href?:string;action?:string}){return <div className="empty"><span className="eyebrow">A LITTLE ROOM FOR SOMETHING GOOD</span><h2>{title}</h2><p>{description}</p><Link className="button" href={href}>{action}<ArrowRight size={18}/></Link></div>}
export function MealCard({item}:{item:Item}){return <article className="meal-card"><Link href={`/menu/${item.id}`} className="meal-image">{item.image?<img src={item.image} alt={item.name} loading="lazy" width="600" height="480"/>:<div className="photo-pending">Óriade<br/><small>Photography coming soon</small></div>}{!item.available&&<span className="image-tag">Currently unavailable</span>}</Link><div className="meal-title"><h3><Link href={`/menu/${item.id}`}>{item.name}</Link></h3><Link href={`/menu/${item.id}`} aria-label={`View ${item.name}`} className="round-link"><ArrowUpRight size={20}/></Link></div><p>{item.description}</p><div className="meal-price">{money(item.price)} <span>per serving</span></div></article>}
