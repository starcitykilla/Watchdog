import customtkinter as ctk
import psutil
import threading
import time
from datetime import datetime # <-- New import for timestamping
from google import genai

# 1. Configure the Gemini Client
client = genai.Client(api_key="YOUR_API_KEY_HERE")

ctk.set_appearance_mode("Dark")  

class SensorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- WINDOW CONFIGURATION ---
        self.title("AI System Monitor")
        self.geometry("500x550") 
        self.attributes("-topmost", True) 
        self.configure(fg_color="#000000") 

        # --- STATE TRACKING ---
        self.is_ai_analyzing = False
        self.temp_threshold = 80.0 
        self.disk_threshold = 90.0 
        
        self.hidden_sensors = set() 
        self.sensor_widgets = {}    
        self.friendly_names = {}    

        # Network speed trackers
        self.last_net_io = psutil.net_io_counters()
        self.last_time = time.time()

        # --- HEADER ROW (Buttons & Status) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=10)

        self.restore_btn = ctk.CTkButton(
            self.header_frame, text="Restore All Sensors", 
            command=self.restore_sensors, fg_color="#4444FF"
        )
        self.restore_btn.pack(side="left")

        self.ai_status_label = ctk.CTkLabel(
            self.header_frame, text="AI Status: Standby", 
            font=("Arial", 14, "bold"), text_color="#00FF00"
        )
        self.ai_status_label.pack(side="right")

        # --- SCROLLABLE SENSOR AREA ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#111111", height=300)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # --- AI ADVICE BOX ---
        self.advice_box = ctk.CTkTextbox(self, height=120, fg_color="#1a1a1a", text_color="#FFFFFF", wrap="word")
        self.advice_box.pack(fill="x", padx=10, pady=10)

        # Start the engine
        self.update_sensors()

    # --- CORE LOGIC ---
    def update_sensors(self):
        metrics = [] 

        try:
            # Gather Temperatures
            temps = psutil.sensors_temperatures()
            for hw_name, entries in temps.items():
                for i, entry in enumerate(entries):
                    metrics.append({
                        "id": f"temp_{hw_name}_{i}",
                        "raw_name": entry.label if entry.label else f"{hw_name} {i}",
                        "display_val": f"{entry.current:.1f} °C",
                        "is_critical": entry.current > self.temp_threshold,
                        "type": "temp"
                    })

            # Gather Disk Usage
            disk = psutil.disk_usage('/')
            metrics.append({
                "id": "disk_main",
                "raw_name": "Main Drive Usage",
                "display_val": f"{disk.percent:.1f} %",
                "is_critical": disk.percent > self.disk_threshold,
                "type": "disk"
            })

            # Gather Network Speeds
            current_time = time.time()
            current_net_io = psutil.net_io_counters()
            time_delta = current_time - self.last_time

            if time_delta > 0:
                dl_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta / (1024 * 1024)
                ul_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta / (1024 * 1024)
                
                metrics.append({
                    "id": "net_dl", "raw_name": "Download Speed", "display_val": f"{dl_speed:.2f} MB/s",
                    "is_critical": False, "type": "net"
                })
                metrics.append({
                    "id": "net_ul", "raw_name": "Upload Speed", "display_val": f"{ul_speed:.2f} MB/s",
                    "is_critical": False, "type": "net"
                })

            self.last_net_io = current_net_io
            self.last_time = current_time

            # Draw the metrics
            for m in metrics:
                sensor_id = m["id"]
                raw_name = m["raw_name"]

                if sensor_id in self.hidden_sensors:
                    continue
                
                if sensor_id not in self.sensor_widgets:
                    self.build_sensor_ui(sensor_id, raw_name)
                    
                    if m["type"] == "temp":
                        cryptic_keywords = ["temp", "package", "composite", "sensor", "id"]
                        if any(k in raw_name.lower() for k in cryptic_keywords):
                            threading.Thread(target=self.get_friendly_name, args=(sensor_id, raw_name)).start()
                
                final_display_name = self.friendly_names.get(sensor_id, raw_name)
                self.sensor_widgets[sensor_id]["label"].configure(text=f"{final_display_name}: {m['display_val']}")

                if m["is_critical"] and not self.is_ai_analyzing:
                    self.trigger_ai_analysis(final_display_name, m["display_val"])

        except Exception as e:
            self.ai_status_label.configure(text="Error reading sensors", text_color="#FF0000")

        self.after(1000, self.update_sensors)

    def build_sensor_ui(self, sensor_id, display_name):
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#222222")
        row_frame.pack(fill="x", pady=2)

        lbl = ctk.CTkLabel(row_frame, text="Loading...", text_color="#FFFF00", font=("Arial", 16, "bold"))
        lbl.pack(side="left", padx=10, pady=5)

        close_btn = ctk.CTkButton(
            row_frame, text="X", width=30, fg_color="#FF4444", hover_color="#CC0000",
            command=lambda s=sensor_id: self.hide_sensor(s)
        )
        close_btn.pack(side="right", padx=10, pady=5)

        self.sensor_widgets[sensor_id] = {"frame": row_frame, "label": lbl}

    def hide_sensor(self, sensor_id):
        self.hidden_sensors.add(sensor_id)
        if sensor_id in self.sensor_widgets:
            self.sensor_widgets[sensor_id]["frame"].destroy()
            del self.sensor_widgets[sensor_id]

    def restore_sensors(self):
        self.hidden_sensors.clear()

    # --- AI NAMING & DIAGNOSTICS ---
    def get_friendly_name(self, sensor_id, raw_name):
        try:
            prompt = f"I am building a Linux hardware monitor on an OptiPlex 7050. I have a sensor with the raw label '{raw_name}'. What is a short, user-friendly 2-word name for this sensor? Return ONLY the short name, no quotes."
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            self.friendly_names[sensor_id] = response.text.strip()
        except Exception:
            pass 

    def trigger_ai_analysis(self, sensor_name, current_val_str):
        self.is_ai_analyzing = True
        self.ai_status_label.configure(text="AI Status: Analyzing...", text_color="#FF0000")
        self.advice_box.delete("0.0", "end")
        self.advice_box.insert("0.0", f"Warning: {sensor_name} at {current_val_str}. Gathering context...\n")
        
        threading.Thread(target=self.get_gemini_diagnosis, args=(sensor_name, current_val_str,)).start()

    def get_gemini_diagnosis(self, sensor_name, current_val_str):
        try:
            ram_usage = psutil.virtual_memory().percent
            prompt = f"My Ubuntu system monitor flagged '{sensor_name}' at {current_val_str}. System RAM is at {ram_usage}%. As an IT expert, give me a brief 3-sentence explanation of what might be causing this issue while live streaming, and 2 bullet points on how to resolve it immediately."
            
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            
            # 1. Update the UI
            self.advice_box.delete("0.0", "end")
            self.advice_box.insert("0.0", response.text)
            self.ai_status_label.configure(text="AI Status: Standby", text_color="#00FF00")

            # 2. Quietly log the event to a text file
            with open("stream_diagnostics.log", "a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                log_file.write(f"[{timestamp}] ALERT: {sensor_name} reached {current_val_str}\n")
                log_file.write(f"RAM Usage at time of alert: {ram_usage}%\n")
                log_file.write(f"AI Diagnosis:\n{response.text}\n")
                log_file.write("-" * 60 + "\n\n")

        except Exception as e:
            self.advice_box.insert("end", f"\nAPI Error: {str(e)}")
            self.is_ai_analyzing = False 

if __name__ == "__main__":
    app = SensorApp()
    app.mainloop()
