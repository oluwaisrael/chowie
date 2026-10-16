import {MealDetail} from '@/features/menu';
import {serverCatalog} from '@/lib/server';
export default async function Page({params}:{params:Promise<{id:string}>}){return <MealDetail id={(await params).id} initialData={await serverCatalog()}/>;}
