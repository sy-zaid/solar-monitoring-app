import os
import time
import shutil
from flask import Flask, render_template
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration
debug_directory = os.getenv("DEBUG_DIRECTORY")

# mqtt_client = mqtt.Client()
# mqtt_client.connect('localhost',1883)
# mqtt_client.publish('Hello',100)


WASMS_API_URL = os.getenv("WASMS_API_URL")
WASMS_API_SECRET = os.getenv("WASMS_API_SECRET")
WASMS_ACCOUNT_ID = os.getenv("WASMS_ACCOUNT_ID")

# print(debug_directory,WASMS_API_URL,WASMS_API_SECRET,WASMS_ACCOUNT_ID)

def get_todays_qpigs_path():
    """Get today's QPIGS file path"""
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today} Serial-QPIGS.log"
    return os.path.join(debug_directory, filename)

# Get today's file path
file_path = get_todays_qpigs_path()
temp_file_path = os.path.join(debug_directory, "temp_Serial-QPIGS.log")

print(f"📁 Monitoring file: {file_path}")

# Global variables
current_inverter_data = {
    'grid_voltage': "0",
    'grid_frequency': "0", 
    'ac_output_voltage': "0",
    'ac_output_frequency': "0",
    'ac_output_power': "0",
    'output_apparent_power': "0",
    'load_percentage': "0",
    'ac_output_percentage': "0",
    'battery_voltage': "0",
    'battery_charging_current': "0",
    'battery_capacity': "0",
    'temperature': "0",
    'pv_input_current': "0",
    'pv_input_voltage': "0",
    'battery_voltage_scc': "0",
    'battery_discharge_current': "0",
    'device_status': "0",
    'battery_voltage_offset': "0",
    'eeprom_version': "0",
    'pv_input_power': "0",
    'device_status2': "0",
    'solar_power': "0",
    'pv_power': "0",
    'unknown': "0",
    'timestamp': 'No data',
    'last_updated': 'Never'
}

file_read_attempts = 0

# Alert tracking to avoid duplicate messages
last_alert_sent = {
    'battery_drain_fast': None,
    'low_battery': None,
    'grid_down': None,
    'battery_drain_limit':None,
    'grid_up':None,
    'insufficient_solar_power':None,
}

app = Flask(__name__)

def get_whatsapp_accounts():
    """Get available WhatsApp accounts from WaSMS.net"""
    try:
        payload = {
            'secret': WASMS_API_SECRET
        }
        
        response = requests.post(
            "https://wasms.net/api/get/wa.accounts",
            data=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            accounts = response.json()
            print("✅ Available WhatsApp accounts:")
            for account in accounts:
                print(f"   📱 Account: {account}")
            return accounts
        else:
            print(f"❌ Failed to get WhatsApp accounts: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting WhatsApp accounts: {e}")
        return None

def send_wasms_whatsapp(message):
    """Send WhatsApp message via WaSMS.net API to multiple recipients"""
    recipients = [
        "+923055663545",  # ✅ Add all target numbers here in E.164 format
    ]
    
    success_count = 0
    for number in recipients:
        try:
            payload = {
                'secret': WASMS_API_SECRET,
                'account': WASMS_ACCOUNT_ID,
                'recipient': number,
                'type': 'text',
                'message': message,
                'priority': 1
            }
            
            print(f"📤 Sending WhatsApp message to {number}")
            response = requests.post(WASMS_API_URL, data=payload, timeout=15)
            
            if response.status_code == 200:
                success_count += 1
                try:
                    response_data = response.json()
                    print(f"✅ Sent to {number} | Response: {response_data}")
                except:
                    print(f"✅ Sent to {number} | Raw response: {response.text}")
            else:
                print(f"❌ Failed to send to {number} | {response.status_code}: {response.text}")
        
        except Exception as e:
            print(f"❌ Error sending to {number}: {e}")

    print(f"📊 WhatsApp message summary: {success_count}/{len(recipients)} successful")
    return success_count > 0

def send_alert(topic, message_code):
    """Send alert to all devices (MQTT + WhatsApp)"""
    successful_sends = 0
    
    # Message mapping for WhatsApp
    whatsapp_messages = {
        '01': f"⚠️ *INVERTER ALERT – BATTERY DRAINING FAST* ⚡️\n\n{message_code}\n\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
        '02': f"🔥 *INVERTER ALERT – BATTERY LOAD LIMIT REACHED* 🚨\n\n{message_code}\n\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
        '03': f"⚠️ *INVERTER ALERT – LOW BATTERY* ⚠️\n\n{message_code}\n\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
        '04': f"🚨 *INVERTER ALERT – K-ELECTRIC POWER OUTAGE* 💡❌\n\n{message_code}\n\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
        '05': f"⚡ *INVERTER ALERT – K-ELECTRIC POWER RESTORED* ✅\n\n{message_code}\n\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
        '06': f"🌥️ *INVERTER ALERT – INSUFFICIENT SOLAR POWER* ☀️🔋\n\n{message_code}\n\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}"
    }

    
    try:
        # Send to MQTT (existing functionality)
        # mqtt_client.publish(topic, message_code)
        print(f"✅ Message sent to MQTT: {topic}, {message_code}")
        successful_sends += 1
    except Exception as e:
        print(f"❌ Failed to send message to MQTT: {e}")
    
    try:
        # Send to WhatsApp via WaSMS
        whatsapp_message = whatsapp_messages.get(topic, f"🔋 INVERTER ALERT\n\n{message_code}\n\nTimestamp: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
        if send_wasms_whatsapp(whatsapp_message):
            successful_sends += 1
            print(f"✅ Message sent to WhatsApp via WaSMS: {topic}")
    except Exception as e:
        print(f"❌ Failed to send message to WhatsApp: {e}")
    
    return successful_sends

cond_1_count = 0
cond_2_count = 0
cond_3_count = 0
cond_6_count = 0
grid_status = True

def check_alerts(parsed_data):
    """Check for various alert conditions and send whatsapp if needed"""
    global last_alert_sent,grid_status
    global cond_1_count,cond_2_count,cond_3_count,cond_6_count
    current_time = time.time()
    alerts_triggered = []
    
    try:
        # Convert string values to appropriate types
        ac_output_power = float(parsed_data.get('ac_output_power', 0))
        battery_capacity = float(parsed_data.get('battery_capacity', 0))
        battery_voltage = float(parsed_data.get('battery_voltage', 0))
        grid_voltage = float(parsed_data.get('grid_voltage', 0))
        pv_power = float(parsed_data.get('pv_power',0))
        battery_discharge_current = float(parsed_data.get('battery_discharge_current',0))

        # ---------------  Alert 01: High Draining Fast (e.g., > 25A), cond_1_count identifies number of times continous alerts sent

        if battery_discharge_current > 25 and cond_1_count < 2 and grid_voltage < 10 and pv_power < 10: 
            if (last_alert_sent['battery_drain_fast'] is None or 
                current_time - last_alert_sent['battery_drain_fast'] > 3):  # 3 sec cooldown
                send_alert('01',f"{ac_output_power}Watts - {battery_discharge_current}A is higher than normal usage and battery will drop faster. Please reduce the load")
                last_alert_sent['battery_drain_fast'] = current_time
                cond_1_count += 1

        # Reset condition for Alert 01
        if battery_discharge_current < 22:
            cond_1_count = 0

        # --------------- 
        # --------------- Alert 02: Battery Load Limit Reached (e.g., < 90A)

        # battery_discharge_current = 100             # 100A for testing
        if battery_discharge_current >= 90 and cond_2_count < 3:               
            if (last_alert_sent['battery_drain_limit'] is None or
                current_time - last_alert_sent['battery_drain_limit'] > 3):  # 3 secs cooldown
                # alerts_triggered.append(f"ALERT! 🚨 BATTERY LOAD LIMIT:\n{battery_discharge_current}A ")
                send_alert('02',f"{ac_output_power}Watts - {battery_discharge_current}A exceeds 90A limit and battery might be damaged if exceeds 100A. Please reduce the load")
                last_alert_sent['battery_drain_limit'] = current_time
                cond_2_count += 1
        
        # Reset condition for Alert 02
        if battery_discharge_current < 80:
            cond_2_count = 0
        
        # --------------- 
        # --------------- Alert 03: Low Battery (e.g., < 23.0)
        if battery_voltage < 23.0:
            if (last_alert_sent['low_battery'] is None or 
                current_time - last_alert_sent['low_battery'] > 3):  # 3 secs cooldown
                # alerts_triggered.append(f"WARNING! ⚠️ LOW BATTERY:\nBattery at {battery_voltage}V - It will shutdown at 21.0V! Reduce the load to keep running for a bit longer")
                send_alert('03',f"{ac_output_power}Watts - {battery_discharge_current}A\nBattery at {battery_voltage}V - It will shutdown at 21.0V! Reduce the load to keep running for a bit longer")
                last_alert_sent['low_battery'] = current_time

        # --------------- 
        # --------------- Alert 04: Grid Down
        if grid_voltage == 0 and grid_status == True:
            if (last_alert_sent['grid_down'] is None or 
                current_time - last_alert_sent['grid_down'] > 3):
                send_alert('04',f"{ac_output_power}Watts - {battery_discharge_current}A")
                last_alert_sent['grid_down'] = current_time
                grid_status = False

        # --------------- 
        # --------------- Alert 05: Grid Up
        if grid_voltage > 210 and grid_status == False:
            if (last_alert_sent['grid_up'] is None or
                current_time - last_alert_sent['grid_up'] > 3):
                send_alert('05',f"{ac_output_power}Watts - {battery_discharge_current}A")
                last_alert_sent['grid_up'] = current_time
                grid_status = True
        
        # ---------------  Alert 06: Insufficient Solar Power 
        if battery_discharge_current >= 3.0 and battery_discharge_current <= 10.0 and cond_6_count <= 2 and grid_voltage < 10 and pv_power < 800 and ac_output_power > 500 and ac_output_power < 1000: 
            if (last_alert_sent['insufficient_solar_power'] is None or 
                current_time - last_alert_sent['insufficient_solar_power'] > 3):  # 3 secs cooldown
                send_alert('06',f"PV Power: {pv_power}Watts - {battery_discharge_current}A\nPlease turn off the fridges or other load.")
                last_alert_sent['insufficient_solar_power'] = current_time
                cond_6_count += 1

        # Reset condition for Alert 06
        if battery_discharge_current < 22:
            cond_6_count = 0    
        
            
    except (ValueError, TypeError) as e:
        print(f"❌ Error processing alerts: {e}")

def parse_inverter_data(data_line):
    """Parse the inverter data line and extract meaningful values"""
    try:
        # Extract the data part - look for opening parenthesis
        start = data_line.find('(')
        if start == -1:
            return None
            
        # Take everything after the opening parenthesis as data
        data_part = data_line[start+1:].strip()
        parts = data_part.split()
        
        print(f"🔍 Parsing {len(parts)} parts: {parts}")
        
        if len(parts) < 21:
            return None
        
        timestamp_str = data_line[1:20] if data_line.startswith('[') else 'Unknown'
        timestamp_obj = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        timestamp_12h = timestamp_obj.strftime("%Y-%m-%d %I:%M:%S %p")

        parsed_data = {
            'grid_voltage': parts[0],
            'grid_frequency': parts[1],
            'ac_output_voltage': parts[2],
            'ac_output_frequency': parts[3],
            'output_apparent_power': parts[4],
            'ac_output_power': parts[5],
            'load_percentage': parts[6],
            'bus_voltage': parts[7],
            'battery_voltage': parts[8],
            'battery_charging_current': parts[9],
            'battery_discharge_current': parts[15],
            'battery_capacity': parts[10],
            'heat_sink_temp': parts[11],
            'pv_voltage': parts[13],
            'pv_power': parts[19],
            'reserved': parts[15],
            'status_bits': parts[16],
            'fan_battery_offset': parts[17],
            'eeprom_fw': parts[18],
            'pv_charging_power': parts[12],
            'device_status': parts[20],
            'timestamp': timestamp_12h,
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Check for alerts after parsing
        check_alerts(parsed_data)
        
        return parsed_data
        
    except Exception as e:
        print(f"Error parsing data: {e}")
        print(f"Data line: {data_line}")
        print(f"Parts: {parts if 'parts' in locals() else 'N/A'}")
        return None
    
def get_latest_inverter_data(lines):
    """Extract the most recent inverter data line (with parentheses)"""
    for line in reversed(lines):
        line = line.strip()
        if line and '(' in line:
            return line
    return None

def copy_and_read_file():
    """Copy the source file to temp location and read it"""
    global file_read_attempts
    
    try:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        shutil.copy2(file_path, temp_file_path)
        file_read_attempts += 1
        
        with open(temp_file_path, "r", errors="ignore") as f:
            content = f.read()
            lines = content.splitlines()
        
        print(f"📋 Copied file (attempt #{file_read_attempts})")
        print(f"📄 Read {len(lines)} lines from temp file")
        return lines
        
    except Exception as e:
        print(f"❌ Error copying/reading file: {e}")
        return None

def monitor_inverter():
    """Monitor the inverter file and update global data"""
    global current_inverter_data, file_read_attempts, file_path
    
    last_size = 0
    last_raw_data = None

    print("🔋 Starting inverter monitoring...")
    
    while True:
        try:
            current_file_path = get_todays_qpigs_path()
            if current_file_path != file_path:
                print(f"🔄 Date changed, switching to: {current_file_path}")
                file_path = current_file_path
                last_size = 0
            
            if not os.path.exists(file_path):
                print("❌ Today's QPIGS file not found!")
                time.sleep(5)
                continue
                
            size = os.path.getsize(file_path)
            print(f"📏 File size: {size} bytes (previous: {last_size})")
            
        except Exception as e:
            print(f"❌ Error checking file: {e}")
            time.sleep(5)
            continue

        if size != last_size or last_raw_data is None:
            print("🔄 File changed or no previous data - processing...")
            last_size = size
            
            lines = copy_and_read_file()
            
            if lines is not None:
                data_line = get_latest_inverter_data(lines)

                if data_line:
                    print("✅ New inverter data found:")
                    print(data_line)
                    last_raw_data = data_line
                    
                    parsed_data = parse_inverter_data(data_line)
                    if parsed_data:
                        current_inverter_data.update(parsed_data)
                        print(f"📊 SUCCESS! Updated web data: {current_inverter_data['ac_output_power']}W, "
                              f"{current_inverter_data['battery_capacity']}% battery, "
                              f"{current_inverter_data['ac_output_voltage']}V")
                    else:
                        print("❌ Failed to parse data for web display")
                else:
                    print("🔍 No inverter data lines found in file")
                    if lines:
                        print("📝 Last 5 lines in file:")
                        for i, line in enumerate(lines[-5:]):
                            print(f"  {i}: '{line}'")
            else:
                print("❌ Failed to read file")
                
        else:
            print("ℹ️ No file change detected")

        print("---")
        time.sleep(5)

@app.route('/')
def index():
    return render_template('index.html', data=current_inverter_data)

@app.route('/api/data')
def api_data():
    """JSON API endpoint for other applications"""
    return current_inverter_data

@app.route('/send-test-whatsapp')
def send_test_whatsapp():
    """Route to test whatsapp functionality"""
    test_message = "🔋 Inverter Monitor Test Alert\nSystem is working correctly!\nTime: " + datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    
    # Test both MQTT and WhatsApp
    mqtt_success = 0
    whatsapp_success = 0
    
    try:
        # mqtt_client.publish('test', 'Test message')
        mqtt_success = 1
        print("✅ Test message sent to MQTT")
    except Exception as e:
        print(f"❌ Failed to send test message to MQTT: {e}")
    
    if send_wasms_whatsapp(test_message):
        whatsapp_success = 1
        print("✅ Test message sent to WhatsApp")
    else:
        print("❌ Failed to send test message to WhatsApp")
    
    return f"Test messages sent - MQTT: {mqtt_success}, WhatsApp: {whatsapp_success}"

@app.route('/get-accounts')
def get_wa_accounts():
    """Route to get available WhatsApp accounts"""
    accounts = get_whatsapp_accounts()
    if accounts:
        return f"Available WhatsApp accounts: {accounts}"
    else:
        return "Failed to get WhatsApp accounts"

def start_web_server():
    """Start the Flask web server"""
    print("🚀 Starting web server...")
    print("📡 Web interface available at: http://localhost:5000")
    print("📊 JSON API available at: http://localhost:5000/api/data")
    print("📱 Test whatsapp available at: http://localhost:5000/send-test-whatsapp")
    print("👥 Get WhatsApp accounts at: http://localhost:5000/get-accounts")
    app.run(host='192.168.18.101', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    print("🔋 Inverter Monitoring System Starting...")
    print(f"📁 Monitoring file: {file_path}")
    
    # First, let's get the WhatsApp accounts to help user configure
    print("🔧 Checking WaSMS.net configuration...")
    get_whatsapp_accounts()
    
    if not os.path.exists(file_path):
        print("❌ Source file not found!")
        exit()
    
    monitor_thread = threading.Thread(target=monitor_inverter, daemon=True)
    monitor_thread.start()
    
    start_web_server()