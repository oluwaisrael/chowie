import {Workspace,OrdersWorkspace} from '@/features/operations';
export default function Page(){return <Workspace title="Delivery tracking."><p className="notice">Track each delivery through kitchen, ready, dispatched and completed. Updates are live status changes; driver GPS/location tracking is not connected.</p><OrdersWorkspace deliveryOnly/></Workspace>}
