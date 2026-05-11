"""
جامع الإحصائيات - تتبع الأداء والسرعة والنجاح
يدعم:
- تخزين البيانات في الوقت الحقيقي
- تحليل السرعة والاستجابة
- تصدير البيانات إلى JSON/CSV
- Dashboard في الوقت الحقيقي
"""

import time
import json
import csv
import os
from collections import deque
from datetime import datetime
import threading
import psutil

class PerformanceStats:
    """إحصائيات الأداء"""
    
    def __init__(self, max_history=1000):
        self.max_history = max_history
        
        # الحلقات الزمنية
        self.response_times = deque(maxlen=max_history)
        self.success_rates = deque(maxlen=max_history)
        self.speed_history = deque(maxlen=max_history)
        
        # العدادات
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = None
        self.last_update = None
        
        # السرعة
        self.current_speed = 0
        self.peak_speed = 0
        self.speed_samples = deque(maxlen=10)
        
        # المقاييس اللحظية
        self.request_times = deque(maxlen=100)
        
    def start(self):
        """بدء جمع الإحصائيات"""
        self.start_time = time.time()
        self.last_update = self.start_time
        
    def record_request(self, response_time=None, success=True):
        """تسجيل طلب واحد"""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        if response_time:
            self.response_times.append(response_time)
            self.request_times.append(response_time)
        
        # تحديث السرعة كل 10 طلبات
        if self.total_requests % 10 == 0:
            self._update_speed()
    
    def _update_speed(self):
        """تحديث السرعة الحالية"""
        now = time.time()
        if self.last_update:
            elapsed = now - self.last_update
            if elapsed > 0:
                speed = 10 / elapsed  # 10 طلبات في الفترة
                self.speed_samples.append(speed)
                
                # المتوسط المتحرك
                if self.speed_samples:
                    self.current_speed = sum(self.speed_samples) / len(self.speed_samples)
                    
                    if self.current_speed > self.peak_speed:
                        self.peak_speed = self.current_speed
        
        self.last_update = now
    
    def get_average_response_time(self):
        """متوسط وقت الاستجابة"""
        if self.response_times:
            return sum(self.response_times) / len(self.response_times)
        return 0
    
    def get_success_rate(self):
        """نسبة النجاح"""
        if self.total_requests == 0:
            return 0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_requests_per_second(self):
        """الطلبات في الثانية"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                return self.total_requests / elapsed
        return 0
    
    def get_eta(self, remaining):
        """الوقت المتبقي"""
        if self.current_speed > 0:
            return remaining / self.current_speed
        return 0
    
    def get_percentile(self, percentile=95):
        """الحصول على النسبة المئوية لوقت الاستجابة"""
        if not self.request_times:
            return 0
        
        sorted_times = sorted(self.request_times)
        index = int(len(sorted_times) * percentile / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    def to_dict(self):
        """تحويل إلى قاموس"""
        return {
            'total_requests': self.total_requests,
            'successful': self.successful_requests,
            'failed': self.failed_requests,
            'success_rate': round(self.get_success_rate(), 2),
            'current_speed': round(self.current_speed, 1),
            'peak_speed': round(self.peak_speed, 1),
            'avg_speed': round(self.get_requests_per_second(), 1),
            'avg_response_time': round(self.get_average_response_time(), 2),
            'p95_response_time': round(self.get_percentile(95), 2),
            'p99_response_time': round(self.get_percentile(99), 2),
            'elapsed': time.time() - self.start_time if self.start_time else 0
        }


class SystemMonitor:
    """مراقبة النظام - CPU, RAM, Network"""
    
    def __init__(self):
        self.cpu_history = deque(maxlen=60)
        self.memory_history = deque(maxlen=60)
        self.network_history = deque(maxlen=60)
        self.last_net_io = psutil.net_io_counters()
        
    def get_current_stats(self):
        """الحصول على إحصائيات النظام الحالية"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_history.append(cpu_percent)
        
        # Memory
        memory = psutil.virtual_memory()
        self.memory_history.append(memory.percent)
        
        # Network
        net_io = psutil.net_io_counters()
        net_speed = {
            'sent': (net_io.bytes_sent - self.last_net_io.bytes_sent) / 1024,
            'recv': (net_io.bytes_recv - self.last_net_io.bytes_recv) / 1024
        }
        self.network_history.append(net_speed)
        self.last_net_io = net_io
        
        return {
            'cpu': {
                'current': cpu_percent,
                'average': sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0,
                'cores': psutil.cpu_count()
            },
            'memory': {
                'percent': memory.percent,
                'used_gb': memory.used / (1024**3),
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3)
            },
            'network': {
                'upload_mbps': net_speed['sent'] / 125,  # KB/s to Mbps
                'download_mbps': net_speed['recv'] / 125
            }
        }


class StatsCollector:
    """جامع الإحصائيات الرئيسي"""
    
    def __init__(self):
        self.performance = PerformanceStats()
        self.system = SystemMonitor()
        self.events = deque(maxlen=1000)
        self.checkpoints = []
        self.running = False
        
    def start(self):
        """بدء الجمع"""
        self.running = True
        self.performance.start()
        
        # بدء thread للتحديث المستمر
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop(self):
        """إيقاف الجمع"""
        self.running = False
        
    def _monitor_loop(self):
        """حلقة المراقبة"""
        while self.running:
            self.collect()
            time.sleep(1)
    
    def collect(self):
        """جمع البيانات"""
        system_stats = self.system.get_current_stats()
        
        # تسجيل نقطة تفتيش كل 10 ثواني
        if len(self.checkpoints) % 10 == 0:
            self.checkpoints.append({
                'timestamp': time.time(),
                'system': system_stats,
                'performance': self.performance.to_dict()
            })
    
    def log_event(self, event_type, message, data=None):
        """تسجيل حدث"""
        self.events.append({
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'data': data
        })
    
    def log_success(self, password, response_time):
        """تسجيل نجاح"""
        self.log_event('success', f'Found password: {password}', {
            'password': password,
            'response_time': response_time
        })
        self.performance.record_request(response_time, True)
    
    def log_failure(self, error):
        """تسجيل فشل"""
        self.log_event('failure', str(error))
        self.performance.record_request(success=False)
    
    def get_full_stats(self):
        """الحصول على جميع الإحصائيات"""
        return {
            'performance': self.performance.to_dict(),
            'system': self.system.get_current_stats(),
            'events': list(self.events)[-50:],  # آخر 50 حدث
            'checkpoints': self.checkpoints[-10:]  # آخر 10 نقاط تفتيش
        }
    
    def export_to_json(self, filename='stats.json'):
        """تصدير إلى JSON"""
        with open(filename, 'w') as f:
            json.dump({
                'performance': self.performance.to_dict(),
                'system_history': {
                    'cpu': list(self.system.cpu_history),
                    'memory': list(self.system.memory_history)
                },
                'events': list(self.events),
                'exported_at': datetime.now().isoformat()
            }, f, indent=2)
        print(f"📊 تم التصدير إلى {filename}")
    
    def export_to_csv(self, filename='stats.csv'):
        """تصدير إلى CSV"""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'speed', 'success_rate', 'total_requests', 'cpu_usage', 'memory_usage'])
            
            for i, checkpoint in enumerate(self.checkpoints):
                writer.writerow([
                    checkpoint['timestamp'],
                    checkpoint['performance'].get('current_speed', 0),
                    checkpoint['performance'].get('success_rate', 0),
                    checkpoint['performance'].get('total_requests', 0),
                    checkpoint['system']['cpu']['current'],
                    checkpoint['system']['memory']['percent']
                ])
        print(f"📊 تم التصدير إلى {filename}")


# أداة Dashboard بسيطة
class SimpleDashboard:
    """Dashboard بسيط في الطرفية"""
    
    def __init__(self, stats_collector):
        self.stats = stats_collector
        
    def display(self):
        """عرض الإحصائيات في الطرفية"""
        stats = self.stats.get_full_stats()
        perf = stats['performance']
        system = stats['system']
        
        # تنظيف الشاشة
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("=" * 60)
        print("🚀 PASSWORD CRACKER ULTRA - DASHBOARD")
        print("=" * 60)
        print(f"📊 الإحصائيات:")
        print(f"   ├─ الطلبات الكلية: {perf['total_requests']:,}")
        print(f"   ├─ الناجحة: {perf['successful']:,}")
        print(f"   ├─ الفاشلة: {perf['failed']:,}")
        print(f"   ├─ نسبة النجاح: {perf['success_rate']}%")
        print(f"   └─ السرعة الحالية: {perf['current_speed']} req/s")
        print()
        print(f"⚡ الأداء:")
        print(f"   ├─ السرعة القصوى: {perf['peak_speed']} req/s")
        print(f"   ├─ متوسط السرعة: {perf['avg_speed']} req/s")
        print(f"   ├─ متوسط وقت الاستجابة: {perf['avg_response_time']}ms")
        print(f"   └─ P95 وقت الاستجابة: {perf['p95_response_time']}ms")
        print()
        print(f"💻 النظام:")
        print(f"   ├─ CPU: {system['cpu']['current']}% (متوسط {system['cpu']['average']:.1f}%)")
        print(f"   ├─ RAM: {system['memory']['percent']}% ({system['memory']['used_gb']:.1f}/{system['memory']['total_gb']:.1f}GB)")
        print(f"   └─ الشبكة: 📤 {system['network']['upload_mbps']:.1f} Mbps / 📥 {system['network']['download_mbps']:.1f} Mbps")
        print("=" * 60)
