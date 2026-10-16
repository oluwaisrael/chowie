import type {MetadataRoute} from 'next';
export default function robots():MetadataRoute.Robots{return {rules:{userAgent:'*',allow:['/','/menu'],disallow:['/api/','/operations','/kitchen','/account','/orders/','/checkout','/reset-password']}};}
