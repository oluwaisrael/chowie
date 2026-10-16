'use client';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {ShoppingBag,Menu,X,ArrowUpRight} from 'lucide-react';
import {useEffect,useState} from 'react';
import {useCart} from '@/lib/cart';
import {useAuth} from './providers';
export function Header(){
  const [open,setOpen]=useState(false);const [ready,setReady]=useState(false);const lines=useCart(s=>s.lines);const {user}=useAuth();const path=usePathname();
  useEffect(()=>{setReady(true);},[]);useEffect(()=>setOpen(false),[path]);
  return <><div className="announcement">GOOD FOOD. GREAT COMPANY. <span>A little taste of home.</span></div><header className="header"><Link className="wordmark" href="/" aria-label="Óriade home">óriade<span>THE NIGERIAN TABLE</span></Link><nav aria-label="Main navigation" className={open?'nav open':'nav'}><Link href="/menu" aria-current={path==='/menu'?'page':undefined}>Our menu</Link><Link href="/#story">Our story</Link><Link href="/#visit">Delivery & pickup</Link><Link href={user?'/account':'/login'}>{user?'My account':'Sign in'}</Link>{user&&user.role!=='customer'&&<Link href={user.role==='kitchen'?'/kitchen':'/operations'}>Workspace</Link>}</nav><div className="header-actions"><Link className="cart-link" href="/cart" aria-label={`Shopping bag, ${ready?lines.reduce((s,l)=>s+l.quantity,0):0} items`}><ShoppingBag size={19}/><span>Bag</span><b>{ready?lines.reduce((s,l)=>s+l.quantity,0):0}</b></Link><button className="icon-button mobile-toggle" aria-label={open?'Close navigation':'Open navigation'} aria-expanded={open} onClick={()=>setOpen(!open)}>{open?<X/>:<Menu/>}</button></div></header></>;
}
export function Footer(){return <footer className="footer"><div className="footer-top"><div><Link href="/" className="wordmark">óriade<span>THE NIGERIAN TABLE</span></Link><p>Rooted in our culture.<br/>Made for your everyday.</p></div><div><h3>Come hungry.</h3><Link href="/menu">Explore the menu <ArrowUpRight size={16}/></Link><Link href="/account">Your orders</Link></div><div><h3>Let’s talk.</h3><a href="https://wa.me/2348066514361" target="_blank" rel="noreferrer">WhatsApp <ArrowUpRight size={16}/></a><a href="tel:+2348066514361">+234 806 651 4361</a></div></div><div className="footer-bottom"><span>© {new Date().getFullYear()} Óriade.</span><span>Nigerian food, thoughtfully made.</span><Link href="/privacy">Privacy</Link></div></footer>}
