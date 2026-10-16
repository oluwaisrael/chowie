import {OrderPage} from '@/features/orders';
export const metadata={title:'Your order',robots:{index:false,follow:false}};
export default async function Page({params}:{params:Promise<{reference:string}>}){return <OrderPage reference={(await params).reference}/>}
