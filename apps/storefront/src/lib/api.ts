let csrf = '';
export function setCsrf(value:string) { csrf = value; }
export async function api<T>(path:string, init:RequestInit = {}):Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type','application/json');
  if (csrf) headers.set('X-CSRF-Token',csrf);
  const response = await fetch(`/api${path}`,{...init,headers,credentials:'same-origin',cache:'no-store'});
  const data = await response.json().catch(()=>({detail:'The service is unavailable. Please try again.'}));
  if (!response.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((issue:{msg?:string})=>issue.msg).filter(Boolean).join(' ') : '';
    throw new Error(detail || 'Please check the form fields and try again.');
  }
  return data;
}
export const json = (data:unknown) => JSON.stringify(data);
