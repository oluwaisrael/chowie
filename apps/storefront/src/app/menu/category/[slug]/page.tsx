import {MenuPage} from '@/features/menu';
import {serverCatalog} from '@/lib/server';
export default async function Page({params}:{params:Promise<{slug:string}>}){return <MenuPage category={(await params).slug} initialData={await serverCatalog()}/>;}
