'use client';
import {ErrorBox} from '@/components/common';
export default function Error({reset}:{reset:()=>void}){return <div className="section"><h1>Let’s try that again.</h1><ErrorBox message="Something interrupted this page. Your saved orders are still in your account." retry={reset}/></div>}
