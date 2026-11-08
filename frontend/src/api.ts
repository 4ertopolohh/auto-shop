import { useEffect, useState } from 'react'
let csrf = ''
export function setCsrf(value:string) { csrf = value }
export async function request<T>(url:string, options:RequestInit = {}):Promise<T> {
  const response = await fetch('/api/'+url, {...options, headers:{'Content-Type':'application/json','X-CSRFToken':csrf,...options.headers}})
  const data = await response.json()
  if (!response.ok) throw new Error(data.error || 'Не удалось загрузить данные. Попробуйте ещё раз.')
  return data as T
}
export function useResource<T>(url:string) {
  const [state,setState] = useState<{data?:T;error?:string;loading:boolean}>({loading:true})
  const [revision,retry] = useState(0)
  useEffect(()=>{
    const controller = new AbortController()
    setState({loading:true})
    request<T>(url,{signal:controller.signal}).then(data=>setState({data,loading:false})).catch((e:Error)=>{if(e.name!=='AbortError')setState({error:e.message,loading:false})})
    return ()=>controller.abort()
  },[url,revision])
  return {...state,retry:()=>retry(n=>n+1)}
}
export const money = (value:string|number)=>new Intl.NumberFormat('ru-RU',{style:'currency',currency:'RUB',maximumFractionDigits:0}).format(Number(value))
