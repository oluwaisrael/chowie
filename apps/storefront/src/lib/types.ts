export type Modifier = {id: string; name: string; price: number; available: boolean};
export type Item = {id:string; name:string; description:string; price:number; image:string; available:boolean; featured:boolean; category_id:string; location_id:string; modifiers:Modifier[]};
export type Catalog = {items:Item[]; categories:{id:string;name:string;slug:string}[]; locations:{id:string;name:string;address:string;active:boolean}[]; zones:{id:string;name:string;fee:number;location_id:string;active:boolean}[]};
export type User = {id:string; name:string; email:string; role:'customer'|'admin'|'operator'|'kitchen';active?:boolean};
export type Order = {reference:string;status:string;version:number;created_at:string;name?:string;phone?:string;address?:string;fulfillment:string;instructions:string;subtotal?:number;delivery_fee?:number;total?:number;whatsapp_url?:string;items:{name:string;quantity:number;unit_price:number;modifiers:{name:string;price:number}[]}[];history:{status:string;at:string}[]};
export type Address = {id:string;label:string;address:string;phone:string};
export const money = (value:number) => new Intl.NumberFormat('en-NG',{style:'currency',currency:'NGN',maximumFractionDigits:value % 100 ? 2 : 0}).format(value / 100);
export const label = (value:string) => value.toLowerCase().replaceAll('_',' ').replace(/^./,s=>s.toUpperCase());
