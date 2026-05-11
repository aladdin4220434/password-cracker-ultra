"""
مدير الـ Proxies - يدعم:
- تناوب الـ proxies تلقائياً
- فحص صحة الـ proxies
- إحصائيات عن أداء كل proxy
- دعم HTTP/HTTPS/SOCKS5
"""

import asyncio
import aiohttp
import random
from collections import deque
from datetime import datetime, timedelta
import json
import os

class ProxyManager:
    """مدير متقدم للـ Proxies"""
    
    def __init__(self, proxy_file=None, max_proxies=1000):
        self.proxies = []
        self.proxy_stats = {}
        self.current_index = 0
        self.max_proxies = max_proxies
        self.proxy_file = proxy_file or "proxies.txt"
        self.load_proxies()
        
    def load_proxies(self):
        """تحميل الـ proxies من الملف"""
        if os.path.exists(self.proxy_file):
            with open(self.proxy_file, 'r') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy and not proxy.startswith('#'):
                        self.add_proxy(proxy)
            print(f"✅ تم تحميل {len(self.proxies)} Proxy")
        else:
            # Proxies افتراضية للاختبار (لن تعمل كلها)
            default_proxies = [
                "http://proxy1.example.com:8080",
                "http://proxy2.example.com:3128",
                "http://proxy3.example.com:80",
            ]
            for proxy in default_proxies:
                self.add_proxy(proxy)
    
    def add_proxy(self, proxy):
        """إضافة Proxy جديد"""
        if proxy not in self.proxies and len(self.proxies) < self.max_proxies:
            self.proxies.append(proxy)
            self.proxy_stats[proxy] = {
                'success_count': 0,
                'fail_count': 0,
                'last_used': None,
                'response_time': [],
                'is_alive': True
            }
    
    def get_next_proxy(self):
        """الحصول على Proxy التالي (Round Robin)"""
        if not self.proxies:
            return None
        
        # البحث عن proxy حي
        for _ in range(len(self.proxies)):
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
            if self.proxy_stats.get(proxy, {}).get('is_alive', True):
                self.proxy_stats[proxy]['last_used'] = datetime.now()
                return proxy
        
        # إذا كلها ميتة، خذ أول واحد
        return self.proxies[0]
    
    def get_random_proxy(self):
        """الحصول على Proxy عشوائي"""
        alive_proxies = [p for p in self.proxies if self.proxy_stats.get(p, {}).get('is_alive', True)]
        if alive_proxies:
            proxy = random.choice(alive_proxies)
            self.proxy_stats[proxy]['last_used'] = datetime.now()
            return proxy
        return self.get_next_proxy()
    
    def report_success(self, proxy, response_time):
        """تسجيل نجاح لـ Proxy"""
        if proxy in self.proxy_stats:
            stats = self.proxy_stats[proxy]
            stats['success_count'] += 1
            stats['response_time'].append(response_time)
            stats['is_alive'] = True
            
            # الاحتفاظ بآخر 100 وقت استجابة فقط
            if len(stats['response_time']) > 100:
                stats['response_time'] = stats['response_time'][-100:]
    
    def report_failure(self, proxy):
        """تسجيل فشل لـ Proxy"""
        if proxy in self.proxy_stats:
            stats = self.proxy_stats[proxy]
            stats['fail_count'] += 1
            
            # إذا فشل 3 مرات متتالية، ضع علامة ميت
            if stats['fail_count'] >= 3:
                stats['is_alive'] = False
    
    def get_best_proxy(self):
        """الحصول على أفضل Proxy بناءً على الأداء"""
        if not self.proxies:
            return None
        
        best_proxy = None
        best_score = -1
        
        for proxy, stats in self.proxy_stats.items():
            if not stats['is_alive']:
                continue
            
            # حساب النقاط: نسبة النجاح × (1 / متوسط وقت الاستجابة)
            total = stats['success_count'] + stats['fail_count']
            if total > 0:
                success_rate = stats['success_count'] / total
                avg_response = sum(stats['response_time']) / len(stats['response_time']) if stats['response_time'] else 1000
                score = success_rate * (1000 / avg_response) if avg_response > 0 else 0
                
                if score > best_score:
                    best_score = score
                    best_proxy = proxy
        
        return best_proxy or self.get_next_proxy()
    
    def get_stats(self):
        """الحصول على إحصائيات الـ Proxies"""
        return {
            'total': len(self.proxies),
            'alive': sum(1 for s in self.proxy_stats.values() if s['is_alive']),
            'dead': sum(1 for s in self.proxy_stats.values() if not s['is_alive']),
            'proxies': self.proxy_stats
        }
    
    async def check_proxy_health(self, proxy, test_url="http://httpbin.org/ip"):
        """فحص صحة Proxy واحد"""
        try:
            start_time = datetime.now()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        self.report_success(proxy, response_time)
                        return True, response_time
        except Exception:
            pass
        
        self.report_failure(proxy)
        return False, None
    
    async def check_all_proxies(self):
        """فحص صحة جميع الـ Proxies"""
        tasks = [self.check_proxy_health(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks)
        
        alive_count = sum(1 for r in results if r[0])
        print(f"🔍 فحص {len(self.proxies)} Proxy - {alive_count} نشط")
        return results
    
    def save_proxies(self, filename=None):
        """حفظ الـ Proxies إلى ملف"""
        filename = filename or self.proxy_file
        with open(filename, 'w') as f:
            for proxy in self.proxies:
                f.write(f"{proxy}\n")
        print(f"💾 تم حفظ {len(self.proxies)} Proxy إلى {filename}")


class SmartProxyMiddleware:
    """وسيط ذكي للـ Proxies - يتكامل مع aiohttp"""
    
    def __init__(self, proxy_manager, rotation_strategy='round_robin'):
        self.proxy_manager = proxy_manager
        self.rotation_strategy = rotation_strategy
        self.failures = {}
        
    def get_proxy(self):
        """الحصول على Proxy حسب الاستراتيجية"""
        if self.rotation_strategy == 'random':
            return self.proxy_manager.get_random_proxy()
        elif self.rotation_strategy == 'best':
            return self.proxy_manager.get_best_proxy()
        else:  # round_robin
            return self.proxy_manager.get_next_proxy()
    
    def report_result(self, proxy, success, response_time=0):
        """تسجيل نتيجة الاستخدام"""
        if success:
            self.proxy_manager.report_success(proxy, response_time)
            self.failures[proxy] = 0
        else:
            self.failures[proxy] = self.failures.get(proxy, 0) + 1
            if self.failures[proxy] >= 3:
                self.proxy_manager.report_failure(proxy)
    
    def get_stats(self):
        """الحصول على الإحصائيات"""
        return self.proxy_manager.get_stats()


# استخدام سريع
if __name__ == "__main__":
    # اختبار
    manager = ProxyManager()
    print(f"📊 الإحصائيات: {manager.get_stats()}")
    
    # الحصول على Proxy
    proxy = manager.get_best_proxy()
    print(f"🔑 أفضل Proxy: {proxy}")
