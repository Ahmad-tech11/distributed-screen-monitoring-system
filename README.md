# Distributed Screen Monitoring System (DSMS)

A Python-based distributed system that allows a central **Master Node** to monitor screenshots from multiple **Worker Nodes** in real time using a **master–worker architecture**. The system demonstrates key concepts of **distributed computing, network communication, and system monitoring**.

---

## Project Overview

The Distributed Screen Monitoring System (DSMS) enables an administrator to remotely monitor multiple machines by periodically receiving screenshots from worker nodes. Each worker captures its screen, compresses the image, and sends it to the master node over TCP. The master node decodes, stores, and organizes the screenshots while tracking worker availability.  

This project is designed as an academic and practical implementation of distributed systems.

---

## Key Features

- Master–Worker distributed architecture  
- Real-time screenshot capture from multiple machines  
- TCP socket-based communication  
- JPEG compression to reduce bandwidth usage  
- Heartbeat mechanism to track worker availability  
- Automatic online/offline worker monitoring  
- Flask-based web dashboard for central monitoring  
- Modular and scalable design  
- Clean separation of master, worker, and shared modules  

---

## Technologies Used

- **Language:** Python  
- **Networking:** TCP Sockets  
- **Web Framework:** Flask  
- **Screen Capture:** MSS  
- **Image Processing:** Pillow  
- **Data Format:** JSON  
- **Operating System:** Windows / Cross-platform  

---

## 📁 Project Structure
distributed-screen-monitoring-system/
├── common/
│ ├── init.py
│ ├── config.py
│ └── protocol.json
├── master/
│ ├── init.py
│ ├── master_server.py
│ ├── dashboard.py
│ └── utils/
│ └── image_decode.py
├── worker/
│ ├── init.py
│ ├── worker_client.py
│ ├── capture.py
│ └── utils/
│ └── compress.py
├── start_master.bat
├── start_worker.bat
├── stop_all.bat
├── .gitignore
└── README.md

---

## ⚙️ How the System Works

1. Worker nodes capture screenshots at regular intervals  
2. Screenshots are compressed into JPEG format  
3. Workers send screenshots and heartbeat timestamps to the master  
4. Master node decodes and stores the images  
5. Worker status is updated based on heartbeat timeout  
6. Flask dashboard displays:
   - Latest screenshots
   - Worker online/offline status
   - Metadata for each worker  

---

## How to Run the Project

### Clone the Repository
```bash
git clone https://github.com/Ahmad-tech11/distributed-screen-monitoring-system.git
cd distributed-screen-monitoring-system

2️⃣ Run the Master Node
pip install -r master/requirements.txt
python master/master_server.py


Dashboard will be available at:   http://localhost:5000

3️⃣ Run the Worker Node
pip install -r worker/requirements.txt
python worker/worker_client.py

Multiple workers can run on different machines or the same machine with different configurations.

🎯 Use Cases

Distributed system monitoring

Remote supervision

Academic projects (Distributed / Parallel Computing)

Network programming demonstrations

🚀 Future Enhancements

Secure communication (TLS/SSL)

Authentication and authorization

Live screen streaming

Cloud storage integration

Cross-platform deployment improvements

👤 Author

Muhammad Ahmad
BS Computer Science
COMSATS University Islamabad, Sahiwal Campus

📄 License

This project is licensed under the MIT License.


