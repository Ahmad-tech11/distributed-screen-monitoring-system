from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    send_from_directory,
    jsonify,
    session,
)
import time
import os
from functools import wraps

app = Flask(__name__)

app.secret_key = "change_this_to_a_random_secret_key"

_workers = None
_change_interval_cb = None
_screen_dir = None

#  SIMPLE AUTH CONFIG
DASHBOARD_USERNAME = "admin"
DASHBOARD_PASSWORD = "admin123"  

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return wrapper

#  HTML TEMPLATES
LOGIN_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Dashboard Login</title>

    <style>
        body {
            margin: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #0d0d0d;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .login-container {
            width: 360px;
            padding: 35px 30px;
            background: rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            box-shadow: 0 0 25px rgba(0, 200, 255, 0.25);
            text-align: center;
            border: 1px solid rgba(0, 200, 255, 0.25);
            animation: fadeIn 0.7s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        .login-container h2 {
            color: #00eaff;
            margin-bottom: 25px;
            font-size: 26px;
            letter-spacing: 1px;
        }

        .error {
            color: #ff4d4d;
            margin-bottom: 12px;
            font-size: 13px;
            font-weight: bold;
        }

        .input-field {
            width: 100%;
            padding: 12px 14px;
            margin-bottom: 18px;
            background: rgba(255, 255, 255, 0.08);
            border: none;
            border-radius: 8px;
            color: #fff;
            font-size: 15px;
            outline: none;
            transition: 0.2s ease;
        }

        .input-field::placeholder {
            color: #b5b5b5;
        }

        .input-field:focus {
            background: rgba(0, 200, 255, 0.15);
            box-shadow: 0 0 5px rgba(0, 200, 255, 0.4);
        }

        .login-btn {
            width: 100%;
            padding: 12px;
            background: #00eaff;
            color: #000;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
            transition: 0.25s ease;
        }

        .login-btn:hover {
            background: #00bcd4;
            box-shadow: 0 0 12px rgba(0, 200, 255, 0.6);
        }
    </style>
</head>

<body>

    <div class="login-container">
        <h2>Dashboard Login</h2>

        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}

        <form method="POST">
            <input type="text" name="username" class="input-field" placeholder="Username" required>
            <input type="password" name="password" class="input-field" placeholder="Password" required>

            <button class="login-btn" type="submit">Login</button>
        </form>
    </div>

</body>
</html>
"""

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Distributed Screenshot Dashboard</title>

    <!-- Chart.js for CPU/RAM graphs -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            transition: background 0.3s, color 0.3s;
        }

        body.light {
            background: #f5f5f5;
            color: #000;
        }
        body.dark {
            background: #121212;
            color: #fff;
        }

        /* Navbar */
        .navbar {
            width: 100%;
            padding: 20px;
            text-align: center;
            font-size: 26px;
            font-weight: 600;
            letter-spacing: 1px;
            background: #1f1f1f;
            color: #00eaff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.4);
            position: relative;
        }

        body.light .navbar {
            background: #e1e1e1;
            color: #0088aa;
        }

        .logout-link {
            position: absolute;
            left: 30px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 13px;
        }
        .logout-link a {
            color: #ffb3b3;
            text-decoration: none;
        }
        .logout-link a:hover {
            text-decoration: underline;
        }

        /* Theme Toggle Button */
        .theme-toggle {
            position: absolute;
            top: 50%;
            right: 30px;
            transform: translateY(-50%);
            background: #00eaff;
            border: none;
            color: #000;
            padding: 8px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 13px;
        }

        .theme-toggle:hover {
            background: #00bcd4;
        }

        /* Top Controls (search + view toggle) */
        .top-controls {
            width: 90%;
            margin: 15px auto 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }

        .search-box input {
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #555;
            background: #1f1f1f;
            color: #fff;
            min-width: 230px;
        }

        body.light .search-box input {
            background: #ffffff;
            color: #000;
            border: 1px solid #aaa;
        }

        .view-toggle button {
            padding: 6px 12px;
            border-radius: 6px;
            border: none;
            margin-left: 5px;
            cursor: pointer;
            font-weight: bold;
        }

        .btn-grid {
            background: #00eaff;
            color: #000;
        }

        .btn-list {
            background: #444;
            color: #fff;
        }

        body.light .btn-list {
            background: #ddd;
            color: #000;
        }

        .btn-grid.active, .btn-list.active {
            box-shadow: 0 0 6px rgba(0,0,0,0.5);
        }

        /* Worker Table */
        .table-container {
            width: 90%;
            margin: 15px auto 30px auto;
            padding: 20px;
            border-radius: 12px;
            background: #1b1b1b;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            transition: background 0.3s;
        }

        body.light .table-container {
            background: #ffffff;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            background: #00eaff;
            color: #000;
            padding: 10px;
            font-size: 14px;
        }

        td {
            padding: 8px;
            border-bottom: 1px solid #444;
            font-size: 13px;
            text-align: center;
        }

        body.light td {
            border-bottom: 1px solid #ccc;
        }

        /* Status Badge */
        .online {
            color: #00ff90;
            font-weight: bold;
        }
        .offline {
            color: #ff4d4d;
            font-weight: bold;
        }

        a.history-link {
            color: #00eaff;
            text-decoration: none;
            font-size: 12px;
        }
        a.history-link:hover {
            text-decoration: underline;
        }

        /* Charts section */
        .charts-section {
            width: 90%;
            margin: 0 auto 20px auto;
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
        }

        .chart-card {
            background: #1b1b1b;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            min-width: 300px;
            flex: 1 1 320px;
        }

        body.light .chart-card {
            background: #ffffff;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }

        .chart-card h3 {
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 16px;
            color: #00eaff;
        }

        body.light .chart-card h3 {
            color: #0088aa;
        }

        /* Screenshot Section */
        .screens-section {
            text-align: center;
            margin-top: 30px;
            font-size: 22px;
            color: #00eaff;
        }

        body.light .screens-section {
            color: #0088aa;
        }

        .card-container {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 15px;
            transition: all 0.3s;
        }

        .card {
            width: 420px;
            margin: 10px;
            padding: 15px;
            border-radius: 14px;
            background: #1b1b1b;
            border: 1px solid #333;
            box-shadow: 0 0 8px rgba(0,0,0,0.4);
            transition: transform .2s, background 0.3s, border 0.3s;
            cursor: pointer;
        }

        body.light .card {
            background: #fff;
            border: 1px solid #ddd;
            box-shadow: 0 0 5px rgba(0,0,0,0.2);
        }

        .card:hover {
            transform: scale(1.02);
        }

        .card h3 {
            font-size: 18px;
            margin-bottom: 6px;
            color: #00eaff;
        }

        body.light .card h3 {
            color: #0088aa;
        }

        .card .meta {
            font-size: 12px;
            color: #aaa;
            margin-bottom: 8px;
        }

        body.light .card .meta {
            color: #555;
        }

        img {
            width: 100%;
            border-radius: 10px;
            border: 1px solid #333;
        }

        body.light img {
            border: 1px solid #ccc;
        }

        .noscreen {
            font-size: 14px;
            padding: 20px;
            color: #ccc;
            text-align: center;
        }

        body.light .noscreen {
            color: #666;
        }

        /* List view for screenshots */
        .card-container.list-view {
            flex-direction: column;
            align-items: center;
        }

        .card-container.list-view .card {
            width: 90%;
            max-width: 900px;
            display: flex;
            gap: 15px;
            align-items: flex-start;
        }

        .card-container.list-view .card img {
            width: 260px;
            max-width: 260px;
        }

        .card-container.list-view .card .text-area {
            flex: 1;
        }

        /* Interval Input */
        input[type=number] {
            padding: 4px;
            width: 70px;
            border-radius: 6px;
            border: 1px solid #555;
            background: #2b2b2b;
            color: #fff;
            font-size: 12px;
        }

        body.light input[type=number] {
            background: #ddd;
            color: #000;
            border: 1px solid #aaa;
        }

        button {
            padding: 5px 10px;
            border-radius: 6px;
            background: #00eaff;
            border: none;
            color: #000;
            font-weight: bold;
            cursor: pointer;
            font-size: 12px;
        }

        button:hover {
            background: #00b8cc;
        }

        /* Fullscreen Modal */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.75);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }

        .modal-overlay.active {
            display: flex;
        }

        .modal-content {
            max-width: 95%;
            max-height: 95%;
        }

        .modal-content img {
            width: 100%;
            height: auto;
            border-radius: 10px;
        }

        .modal-close {
            position: absolute;
            top: 15px;
            right: 20px;
            font-size: 26px;
            color: white;
            cursor: pointer;
        }
    </style>

</head>
<body class="dark">

    <div class="navbar">
        <div class="logout-link">
            <a href="{{ url_for('logout') }}">Logout</a>
        </div>
        DISTRIBUTED SCREENSHOT MONITORING DASHBOARD
        <button class="theme-toggle" onclick="toggleTheme()">Toggle Theme</button>
    </div>

    <div class="top-controls">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search worker by ID..." oninput="filterWorkers()">
        </div>
        <div class="view-toggle">
            <button class="btn-grid active" id="gridBtn" onclick="setGridView()">Grid View</button>
            <button class="btn-list" id="listBtn" onclick="setListView()">List View</button>
        </div>
    </div>

    <div class="table-container">
        <table>
            <tr>
                <th>Worker ID</th>
                <th>Status</th>
                <th>Last Seen</th>
                <th>Interval (s)</th>
                <th>CPU</th>
                <th>RAM</th>
                <th>Uptime</th>
                <th>Change Interval</th>
                <th>History</th>
            </tr>
            {% for w in workers %}
            <tr id="row-{{ w.worker_id }}" data-worker-id="{{ w.worker_id|lower }}">
                <td>{{ w.worker_id }}</td>
                <td id="status-{{ w.worker_id }}" class="{{ 'online' if w.status == 'online' else 'offline' }}">{{ w.status }}</td>
                <td id="lastseen-{{ w.worker_id }}">{{ w.last_seen_human }}</td>
                <td id="interval-{{ w.worker_id }}">{{ w.current_interval }}</td>
                <td id="cpu-{{ w.worker_id }}">{{ w.cpu }}</td>
                <td id="ram-{{ w.worker_id }}">{{ w.ram }}</td>
                <td id="uptime-{{ w.worker_id }}">{{ w.uptime }}</td>
                <td>
                    <form method="post" action="{{ url_for('set_interval', worker_id=w.worker_id) }}">
                        <input type="number" step="0.1" name="interval" value="{{ w.current_interval }}" />
                        <button type="submit">Update</button>
                    </form>
                </td>
                <td>
                    <a class="history-link" href="{{ url_for('history', worker_id=w.worker_id) }}">View</a>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <!-- CPU / RAM GRAPHS -->
    <div class="charts-section">
        <div class="chart-card">
            <h3>Average CPU Usage (%)</h3>
            <canvas id="cpuChart"></canvas>
        </div>
        <div class="chart-card">
            <h3>Average RAM Usage (%)</h3>
            <canvas id="ramChart"></canvas>
        </div>
    </div>

    <div class="screens-section">Live Screenshots</div>

    <div class="card-container" id="cardContainer">
        {% for w in workers %}
        <div class="card"
             id="card-{{ w.worker_id }}"
             data-worker-id="{{ w.worker_id|lower }}"
             onclick="openModal('{{ url_for('serve_screen', filename=w.last_image_filename) if w.last_image_filename else '' }}')">
            <div class="text-area">
                <h3>{{ w.worker_id }} — <span id="card-status-{{ w.worker_id }}">{{ w.status }}</span></h3>
                <div class="meta">
                    Last seen: <span id="card-lastseen-{{ w.worker_id }}">{{ w.last_seen_human }}</span> |
                    Interval: <span id="card-interval-{{ w.worker_id }}">{{ w.current_interval }}</span>s
                    <br>
                    CPU: <span id="card-cpu-{{ w.worker_id }}">{{ w.cpu }}</span> |
                    RAM: <span id="card-ram-{{ w.worker_id }}">{{ w.ram }}</span> |
                    Uptime: <span id="card-uptime-{{ w.worker_id }}">{{ w.uptime }}</span>
                </div>
            </div>
            {% if w.last_image_filename %}
                <img id="img-{{ w.worker_id }}" src="{{ url_for('serve_screen', filename=w.last_image_filename) }}" alt="Screenshot">
            {% else %}
                <div class="noscreen">No Screenshot Available</div>
            {% endif %}
        </div>
        {% endfor %}
    </div>

    <!-- Fullscreen Modal -->
    <div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
        <div class="modal-close" onclick="closeModal(event)">×</div>
        <div class="modal-content">
            <img id="modalImg" src="" alt="Fullscreen Screenshot">
        </div>
    </div>

    <!-- Offline alert + Charts + AJAX -->
    <script>
        let previousStatus = {};
        let cpuChart, ramChart;
        let chartLabels = [];
        let cpuData = [];
        let ramData = [];

        function toggleTheme() {
            let body = document.body;
            if (body.classList.contains("dark")) {
                body.classList.remove("dark");
                body.classList.add("light");
                localStorage.setItem("dashboardTheme", "light");
            } else {
                body.classList.remove("light");
                body.classList.add("dark");
                localStorage.setItem("dashboardTheme", "dark");
            }
        }

        function initCharts() {
            const cpuCtx = document.getElementById("cpuChart").getContext("2d");
            const ramCtx = document.getElementById("ramChart").getContext("2d");

            cpuChart = new Chart(cpuCtx, {
                type: "line",
                data: {
                    labels: chartLabels,
                    datasets: [{
                        label: "Avg CPU (%)",
                        data: cpuData,
                        borderWidth: 2,
                        tension: 0.2
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });

            ramChart = new Chart(ramCtx, {
                type: "line",
                data: {
                    labels: chartLabels,
                    datasets: [{
                        label: "Avg RAM (%)",
                        data: ramData,
                        borderWidth: 2,
                        tension: 0.2
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }

        // Load saved theme on startup
        window.onload = () => {
            const saved = localStorage.getItem("dashboardTheme");
            if (saved) {
                document.body.className = saved;
            }
            initCharts();
            startAutoRefresh();
        };

        function setGridView() {
            const cont = document.getElementById("cardContainer");
            cont.classList.remove("list-view");
            document.getElementById("gridBtn").classList.add("active");
            document.getElementById("listBtn").classList.remove("active");
        }

        function setListView() {
            const cont = document.getElementById("cardContainer");
            cont.classList.add("list-view");
            document.getElementById("gridBtn").classList.remove("active");
            document.getElementById("listBtn").classList.add("active");
        }

        function filterWorkers() {
            const query = document.getElementById("searchInput").value.toLowerCase();
            const rows = document.querySelectorAll("[id^='row-']");
            const cards = document.querySelectorAll("[id^='card-']");

            rows.forEach(row => {
                const wid = row.getAttribute("data-worker-id") || "";
                row.style.display = wid.includes(query) ? "" : "none";
            });

            cards.forEach(card => {
                const wid = card.getAttribute("data-worker-id") || "";
                card.style.display = wid.includes(query) ? "" : "none";
            });
        }

        // Fullscreen modal
        function openModal(imgUrl) {
            if (!imgUrl) return;
            const overlay = document.getElementById("modalOverlay");
            const img = document.getElementById("modalImg");
            img.src = imgUrl;
            overlay.classList.add("active");
        }

        function closeModal(event) {
            if (event && event.target && event.target.id === "modalImg") {
                return;
            }
            const overlay = document.getElementById("modalOverlay");
            overlay.classList.remove("active");
        }

        // Offline alert beep
        function playBeep() {
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = ctx.createOscillator();
                const gain = ctx.createGain();
                oscillator.type = "sine";
                oscillator.frequency.setValueAtTime(880, ctx.currentTime);
                gain.gain.setValueAtTime(0.1, ctx.currentTime);

                oscillator.connect(gain);
                gain.connect(ctx.destination);

                oscillator.start();
                oscillator.stop(ctx.currentTime + 0.3);
            } catch (e) {
                console.log("AudioContext error:", e);
            }
        }

        // Auto-refresh via AJAX
        function startAutoRefresh() {
            setInterval(fetchStatus, 5000);
        }

        function fetchStatus() {
            fetch("{{ url_for('api_status') }}")
                .then(resp => resp.json())
                .then(data => {
                    if (!data || !data.workers) return;

                    let sumCpu = 0;
                    let sumRam = 0;
                    let countCpu = 0;
                    let countRam = 0;

                    data.workers.forEach(w => {
                        const id = w.worker_id;

                        // Detect status change for beep
                        const prev = previousStatus[id];
                        if (prev === "online" && w.status === "offline") {
                            playBeep();
                        }
                        previousStatus[id] = w.status;

                        // Table cells
                        const st = document.getElementById("status-" + id);
                        const ls = document.getElementById("lastseen-" + id);
                        const it = document.getElementById("interval-" + id);
                        const cpu = document.getElementById("cpu-" + id);
                        const ram = document.getElementById("ram-" + id);
                        const up = document.getElementById("uptime-" + id);

                        if (st) {
                            st.textContent = w.status;
                            st.className = w.status === "online" ? "online" : "offline";
                        }
                        if (ls) ls.textContent = w.last_seen_human;
                        if (it) it.textContent = w.current_interval;
                        if (cpu) cpu.textContent = w.cpu;
                        if (ram) ram.textContent = w.ram;
                        if (up) up.textContent = w.uptime;

                        // Cards
                        const cst = document.getElementById("card-status-" + id);
                        const cls = document.getElementById("card-lastseen-" + id);
                        const cit = document.getElementById("card-interval-" + id);
                        const ccpu = document.getElementById("card-cpu-" + id);
                        const cram = document.getElementById("card-ram-" + id);
                        const cup = document.getElementById("card-uptime-" + id);
                        const img = document.getElementById("img-" + id);

                        if (cst) cst.textContent = w.status;
                        if (cls) cls.textContent = w.last_seen_human;
                        if (cit) cit.textContent = w.current_interval;
                        if (ccpu) ccpu.textContent = w.cpu;
                        if (cram) cram.textContent = w.ram;
                        if (cup) cup.textContent = w.uptime;

                        if (img && w.last_image_url) {
                            img.src = w.last_image_url + "?t=" + new Date().getTime();
                        }

                        const card = document.getElementById("card-" + id);
                        if (card && w.last_image_url) {
                            card.setAttribute("onclick", "openModal('" + w.last_image_url + "')");
                        }

                        // For charts: accumulate avg CPU/RAM
                        const cpuVal = parseFloat(w.cpu);
                        const ramVal = parseFloat(w.ram);
                        if (!isNaN(cpuVal)) {
                            sumCpu += cpuVal;
                            countCpu++;
                        }
                        if (!isNaN(ramVal)) {
                            sumRam += ramVal;
                            countRam++;
                        }
                    });

                    const avgCpu = countCpu > 0 ? (sumCpu / countCpu) : null;
                    const avgRam = countRam > 0 ? (sumRam / countRam) : null;

                    const label = new Date().toLocaleTimeString();
                    chartLabels.push(label);
                    if (chartLabels.length > 20) {
                        chartLabels.shift();
                    }

                    if (avgCpu !== null) {
                        cpuData.push(avgCpu);
                        if (cpuData.length > 20) cpuData.shift();
                    } else {
                        cpuData.push(0);
                        if (cpuData.length > 20) cpuData.shift();
                    }

                    if (avgRam !== null) {
                        ramData.push(avgRam);
                        if (ramData.length > 20) ramData.shift();
                    } else {
                        ramData.push(0);
                        if (ramData.length > 20) ramData.shift();
                    }

                    cpuChart.update();
                    ramChart.update();
                })
                .catch(err => {
                    console.log("Error fetching status:", err);
                });
        }
    </script>

</body>
</html>
"""


HISTORY_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Screenshot History - {{ worker_id }}</title>
    <style>
        body {
            margin: 0;
            background: #121212;
            color: #fff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .navbar {
            width: 100%;
            padding: 15px;
            background: #1f1f1f;
            color: #00eaff;
            font-size: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar a {
            color: #ccc;
            text-decoration: none;
            font-size: 13px;
        }
        .navbar a:hover {
            text-decoration: underline;
        }
        .container {
            width: 90%;
            margin: 20px auto;
        }
        h2 {
            margin-bottom: 10px;
        }
        .grid {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }
        .item {
            width: 260px;
            background: #1b1b1b;
            border-radius: 10px;
            padding: 8px;
            box-shadow: 0 0 6px rgba(0,0,0,0.5);
            font-size: 12px;
        }
        .item img {
            width: 100%;
            border-radius: 8px;
            border: 1px solid #333;
        }
        .timestamp {
            margin-top: 5px;
            color: #aaa;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div>History: {{ worker_id }}</div>
        <div>
            <a href="{{ url_for('index') }}">← Back to Dashboard</a>
            &nbsp;|&nbsp;
            <a href="{{ url_for('logout') }}">Logout</a>
        </div>
    </div>
    <div class="container">
        <h2>Screenshots for {{ worker_id }}</h2>
        {% if screenshots %}
        <div class="grid">
            {% for s in screenshots %}
            <div class="item">
                <a href="{{ s.url }}" target="_blank">
                    <img src="{{ s.url }}" alt="screenshot">
                </a>
                <div class="timestamp">{{ s.time_str }}</div>
            </div>
            {% endfor %}
        </div>
        {% else %}
            <p>No screenshots found for this worker.</p>
        {% endif %}
    </div>
</body>
</html>
"""

# Flask Dashboard Logic

def init(workers_dict, change_interval_callback, screen_dir):
    global _workers, _change_interval_cb, _screen_dir
    _workers = workers_dict
    _change_interval_cb = change_interval_callback
    _screen_dir = screen_dir


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password."
    return render_template_string(LOGIN_TEMPLATE, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    workers_view = []
    for wid, info in list(_workers.items()):
        ts = info.get("last_timestamp", 0)
        if ts > 0:
            last_seen_human = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        else:
            last_seen_human = "Never"

        workers_view.append(
            type(
                "W",
                (),
                {
                    "worker_id": wid,
                    "status": info.get("status", "offline"),
                    "last_seen_human": last_seen_human,
                    "current_interval": info.get("current_interval", 0),
                    "last_image_filename": info.get("last_image_filename"),
                    "cpu": info.get("cpu", "N/A"),
                    "ram": info.get("ram", "N/A"),
                    "uptime": info.get("uptime", "N/A"),
                },
            )
        )

    return render_template_string(HTML_TEMPLATE, workers=workers_view)


@app.route("/set_interval/<worker_id>", methods=["POST"])
@login_required
def set_interval(worker_id):
    try:
        new_interval = float(request.form.get("interval", "2"))
    except ValueError:
        new_interval = 2.0

    if _change_interval_cb:
        _change_interval_cb(worker_id, new_interval)

    return redirect(url_for("index"))


@app.route("/screens/<path:filename>")
@login_required
def serve_screen(filename):
    return send_from_directory(_screen_dir, filename)


@app.route("/history/<worker_id>")
@login_required
def history(worker_id):
    screenshots = []

    if _screen_dir and os.path.isdir(_screen_dir):
        for fname in os.listdir(_screen_dir):

            if not fname.lower().endswith(".jpg"):
                continue

            if not fname.startswith(worker_id + "_"):
                continue

            try:
                name_part = fname.rsplit(".", 1)[0]
                ts_part = name_part.split("_")[-1]
                ts_val = int(ts_part)

                # 🔥 milliseconds → seconds
                if ts_val > 10_000_000_000:
                    ts_val = ts_val / 1000

                time_str = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(ts_val)
                )
            except Exception:
                ts_val = 0
                time_str = "Unknown time"

            screenshots.append(
                {
                    "filename": fname,
                    "url": url_for("serve_screen", filename=fname),
                    "timestamp": ts_val,
                    "time_str": time_str,
                }
            )

        screenshots.sort(key=lambda x: x["timestamp"], reverse=True)

    return render_template_string(
        HISTORY_TEMPLATE,
        worker_id=worker_id,
        screenshots=screenshots
    )

@app.route("/api/status")
@login_required
def api_status():
    """
    JSON endpoint for AJAX live updates.
    """
    workers_list = []
    for wid, info in list(_workers.items()):
        ts = info.get("last_timestamp", 0)
        if ts > 0:
            last_seen_human = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        else:
            last_seen_human = "Never"

        last_image_filename = info.get("last_image_filename")
        last_image_url = None
        if last_image_filename:
            last_image_url = url_for("serve_screen", filename=last_image_filename)

        workers_list.append(
            {
                "worker_id": wid,
                "status": info.get("status", "offline"),
                "last_seen_human": last_seen_human,
                "current_interval": info.get("current_interval", 0),
                "cpu": info.get("cpu", "N/A"),
                "ram": info.get("ram", "N/A"),
                "uptime": info.get("uptime", "N/A"),
                "last_image_url": last_image_url,
            }
        )

    return jsonify({"workers": workers_list})


def start(port):
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
