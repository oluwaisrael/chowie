'use client';
import {QueryClient,QueryClientProvider,useQuery} from '@tanstack/react-query';
import {createContext,useContext,useState,useEffect} from 'react';
import {api,setCsrf} from '@/lib/api';
import type {User} from '@/lib/types';
const AuthContext=createContext<{user:User|null;loading:boolean;refresh:()=>void}>({user:null,loading:true,refresh:()=>{}});
function Auth({children}:{children:React.ReactNode}) {
  const query=useQuery({queryKey:['me'],queryFn:()=>api<{user:User;csrf:string}>('/auth/me'),retry:false,staleTime:60_000});
  useEffect(()=>{setCsrf(query.data?.csrf||'');},[query.data]);
  return <AuthContext.Provider value={{user:query.data?.user||null,loading:query.isLoading,refresh:()=>{void query.refetch();}}}>{children}</AuthContext.Provider>;
}
export const useAuth=()=>useContext(AuthContext);
export function Providers({children}:{children:React.ReactNode}) {
  const [client]=useState(()=>new QueryClient({defaultOptions:{queries:{retry:1,staleTime:30_000}}}));
  return <QueryClientProvider client={client}><Auth>{children}</Auth></QueryClientProvider>;
}
