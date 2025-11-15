import os
import time
import shutil

file_path = r"C:\Users\syedm\WatchPower\log\debug\2025-10-11 Serial-QPIGS.log"
temp_file_path = r"C:\Users\syedm\WatchPower\log\debug\temp_Serial-QPIGS.log"

print(f"Monitoring file:\n{file_path}\n")
print(f"Temp file:\n{temp_file_path}\n")

if not os.path.exists(file_path):
    print("❌ Source file not found!")
    exit()

last_size = 0
last_data = None
file_read_attempts = 0

def get_latest_inverter_data(lines):
    """Extract the most recent inverter data line (with parentheses)"""
    for line in reversed(lines):
        line = line.strip()
        # Only consider lines that contain both timestamp AND inverter data in parentheses
        if line and '(' in line and ')' in line:
            return line
    return None

def copy_and_read_file():
    """Copy the source file to temp location and read it"""
    global file_read_attempts
    
    try:
        # Remove temp file if it exists
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print("🗑️  Removed old temp file")
        
        # Copy the file
        shutil.copy2(file_path, temp_file_path)
        file_read_attempts += 1
        print(f"📋 Copied file (attempt #{file_read_attempts})")
        
        # Read the temp file
        with open(temp_file_path, "r", errors="ignore") as f:
            content = f.read()
            lines = content.splitlines()
        
        print(f"📄 Read {len(lines)} lines from temp file")
        return lines
        
    except Exception as e:
        print(f"❌ Error copying/reading file: {e}")
        return None

while True:
    try:
        # Check if source file exists and get its size
        if not os.path.exists(file_path):
            print("❌ Source file not found!")
            time.sleep(3)
            continue
            
        size = os.path.getsize(file_path)
        print(f"📏 File size: {size} bytes (previous: {last_size})")
        
    except Exception as e:
        print(f"❌ Error checking file: {e}")
        time.sleep(3)
        continue

    if size != last_size or last_data is None:
        print("🔄 File changed or no previous data - processing...")
        last_size = size
        
        # Copy and read the file
        lines = copy_and_read_file()
        
        if lines is not None:
            # Get the latest actual inverter data line
            data_line = get_latest_inverter_data(lines)

            if data_line:
                print("✅ New inverter data found:")
                print(data_line)
                last_data = data_line
            else:
                print("🔍 No inverter data lines found in file")
                # Debug: show what lines we found
                if lines:
                    print("📝 Lines found in file:")
                    for i, line in enumerate(lines[-5:]):  # Show last 5 lines
                        print(f"  {i}: '{line}'")
                
                if last_data:
                    print("⚠️ No new inverter data — showing last known:")
                    print(last_data)
                else:
                    print("⏳ No valid inverter data yet...")
        else:
            print("❌ Failed to read file")
            if last_data:
                print("⚠️ Using last known data due to read error:")
                print(last_data)
    else:
        if last_data:
            print("ℹ️ No file change — showing last known:")
            print(last_data)
        else:
            print("⏳ Waiting for inverter data...")

    print("---")  # Separator for readability
    time.sleep(5)  # Increased to 5 seconds to match your example