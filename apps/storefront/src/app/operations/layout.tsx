import {StaffGuard} from '@/features/operations';
export const metadata={title:'Restaurant operations',robots:{index:false,follow:false}};
export default function Layout({children}:{children:React.ReactNode}){return <StaffGuard>{children}</StaffGuard>}
