import {MenuPage} from '@/features/menu';
import {serverCatalog} from '@/lib/server';
export const metadata={title:'Our menu'};
export default async function Page(){return <MenuPage initialData={await serverCatalog()}/>;}
