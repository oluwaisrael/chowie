'use client';
import {useEffect,useRef,useState} from 'react';
export function useLive<T>(path:string|null,onSnapshot:(data:T)=>void,token?:string){
 const callback=useRef(onSnapshot);useEffect(()=>{callback.current=onSnapshot;},[onSnapshot]);const [connected,setConnected]=useState(false);
 useEffect(()=>{if(!path)return;const controller=new AbortController();let stopped=false;let timer:ReturnType<typeof setTimeout>;
 async function connect(){try{const response=await fetch(`/api${path}`,{headers:token?{'X-Order-Token':token}:{},signal:controller.signal,cache:'no-store'});if(!response.ok||!response.body)throw new Error('Connection unavailable');setConnected(true);const reader=response.body.getReader();const decoder=new TextDecoder();let buffer='';while(!stopped){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let end;while((end=buffer.indexOf('\n\n'))>=0){const block=buffer.slice(0,end);buffer=buffer.slice(end+2);if(block.startsWith('event: expired')){stopped=true;break;}const line=block.split('\n').find(l=>l.startsWith('data: '));if(line)callback.current(JSON.parse(line.slice(6)));}}}catch{}finally{setConnected(false);if(!stopped)timer=setTimeout(connect,5000);}}
 void connect();return()=>{stopped=true;controller.abort();clearTimeout(timer);};},[path,token]);return connected;
}
