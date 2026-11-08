import React,{lazy,Suspense,useEffect} from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter,Routes,Route,useLocation } from 'react-router-dom'
import Layout from './components/Layout'
import { Loading,ErrorBox } from './components/UI'
import { CartProvider } from './store'
import { setCsrf,useResource } from './api'
import type { Config } from './types'
import './styles/global.scss'
const Home=lazy(()=>import('./pages/Home'))
const Catalog=lazy(()=>import('./pages/Catalog'))
const ProductPage=lazy(()=>import('./pages/Product'))
const Cart=lazy(()=>import('./pages/Cart'))
const Checkout=lazy(()=>import('./pages/Checkout'))
const Info=lazy(()=>import('./pages/Info'))
function App(){
  const {data:config,error,retry}=useResource<Config>('bootstrap/');const location=useLocation()
  useEffect(()=>{if(config){setCsrf(config.csrf);document.title=config.seo_title;document.querySelector('meta[name="description"]')?.setAttribute('content',config.seo_description);document.querySelector('meta[name="robots"]')?.setAttribute('content',config.allow_indexing?'index,follow':'noindex,nofollow');const link=document.querySelector('link[rel="canonical"]')||document.head.appendChild(document.createElement('link'));link.setAttribute('rel','canonical');link.setAttribute('href',config.canonical_url.replace(/\/$/,'')+location.pathname)}},[config,location.pathname])
  if(error)return <div className="container section"><ErrorBox message={error} retry={retry}/></div>
  if(!config)return <div className="container section"><Loading/></div>
  return <Routes><Route element={<Layout config={config}/>}><Route index element={<Suspense fallback={<Loading/>}><Home/></Suspense>}/><Route path="catalog" element={<Suspense fallback={<Loading/>}><Catalog/></Suspense>}/><Route path="product/:slug" element={<Suspense fallback={<Loading/>}><ProductPage/></Suspense>}/><Route path="cart" element={<Suspense fallback={<Loading/>}><Cart/></Suspense>}/><Route path="checkout" element={<Suspense fallback={<Loading/>}><Checkout/></Suspense>}/><Route path="delivery" element={<Suspense fallback={<Loading/>}><Info type="delivery"/></Suspense>}/><Route path="about" element={<Suspense fallback={<Loading/>}><Info type="about"/></Suspense>}/><Route path="*" element={<Suspense fallback={<Loading/>}><Info type="404"/></Suspense>}/></Route></Routes>
}
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><BrowserRouter><CartProvider><App/></CartProvider></BrowserRouter></React.StrictMode>)
