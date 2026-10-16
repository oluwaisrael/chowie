'use client';
import {create} from 'zustand';
import {persist} from 'zustand/middleware';
import type {Item} from './types';
export type CartLine = {key:string;item_id:string;name:string;image:string;price:number;quantity:number;modifiers:string[];modifierNames:string[];location_id:string};
export const cartKey = (id:string,modifiers:string[]) => `${id}:${[...modifiers].sort().join(',')}`;
export const cartTotal = (lines:CartLine[]) => lines.reduce((total,line)=>total+line.price*line.quantity,0);
export const useCart = create<{lines:CartLine[];add:(item:Item,mods:string[],quantity:number)=>void;quantity:(key:string,n:number)=>void;clear:()=>void}>()(persist((set)=>({
  lines:[],
  add:(item,mods,quantity)=>set(state=>{
    const key=cartKey(item.id,mods); const selected=item.modifiers.filter(m=>mods.includes(m.id));
    const old=state.lines.find(l=>l.key===key);
    if(old) return {lines:state.lines.map(l=>l.key===key?{...l,quantity:Math.min(20,l.quantity+quantity)}:l)};
    return {lines:[...state.lines,{key,item_id:item.id,name:item.name,image:item.image,price:item.price+selected.reduce((s,m)=>s+m.price,0),quantity,modifiers:mods,modifierNames:selected.map(m=>m.name),location_id:item.location_id}]};
  }),
  quantity:(key,n)=>set(state=>({lines:n<=0?state.lines.filter(l=>l.key!==key):state.lines.map(l=>l.key===key?{...l,quantity:Math.min(20,n)}:l)})),
  clear:()=>set({lines:[]}),
}),{name:'oriade-cart',version:1}));
