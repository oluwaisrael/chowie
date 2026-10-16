import 'server-only';
import type {Catalog} from './types';
export async function serverCatalog():Promise<Catalog|undefined>{
  try{
    const response=await fetch(`${process.env.API_INTERNAL_URL||'http://127.0.0.1:8000'}/catalog`,{cache:'no-store',signal:AbortSignal.timeout(5000)});
    return response.ok?await response.json():undefined;
  }catch{return undefined;}
}
