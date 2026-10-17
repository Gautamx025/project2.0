'use client';
import {useCallback,useEffect,useState} from 'react';
import {api,Job} from './api';
export function useLedger(){
  const [jobs,setJobs]=useState<Job[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState('');
  const refresh=useCallback(async()=>{try{setJobs(await api<Job[]>('/jobs'));setError('');}catch(reason){setError((reason as Error).message);}finally{setLoading(false);}},[]);
  useEffect(()=>{refresh();const timer=setInterval(refresh,2500);return()=>clearInterval(timer);},[refresh]);
  return {jobs,loading,error,refresh};
}
export function statusLabel(job:Job){return ({queued:'In queue',processing:'Developing',ready:'Draft ready',published:job.store_result?.demo?'Demo draft saved':'Store draft synced',failed:'Needs a retry',cancelled:'Cancelled'})[job.status];}
