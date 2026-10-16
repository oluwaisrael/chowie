import type {Metadata} from 'next';
import './globals.css';
import {Providers} from '@/components/providers';
import {Header,Footer} from '@/components/shell';
export const metadata:Metadata={title:{default:'Óriade — The Nigerian Table',template:'%s | Óriade'},description:'Nigerian flavours, thoughtfully made. Explore the Óriade menu and order for delivery or pickup with a personal WhatsApp confirmation.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><Providers><a className="skip-link" href="#main">Skip to content</a><Header/><main id="main">{children}</main><Footer/></Providers></body></html>}
