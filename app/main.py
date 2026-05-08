from datetime import timedelta

from flask import Flask, jsonify, request, render_template_string, session, redirect
import mysql.connector
from mysql.connector import pooling
import os
from datetime import timedelta


app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")





app.config.update( #fix cookie
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7)
)

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "cadetcoin")

LOGIN_USERNAME = os.getenv("LOGIN_USERNAME", "cadet.demo")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "demo")

pool = None


def init_database():
    global pool

    last_error = None

    for attempt in range(30):
        try:
            pool = pooling.MySQLConnectionPool(
                pool_name="cadetcoin_pool",
                pool_size=5,
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )

            conn = pool.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    coins INT NOT NULL DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    coin_value INT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    activity_id INT NOT NULL,
                    notes TEXT,
                    coins_earned INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (activity_id) REFERENCES activities(id)
                )
            """)

            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO users (name, coins) VALUES (%s, %s)",
                    ("Cadet", 0)
                )

            cursor.execute("SELECT COUNT(*) FROM activities")
            if cursor.fetchone()[0] == 0:
                default_activities = [
                    ("Recorded Run", 10),
                    ("Company Workout", 15),
                    ("Improved AFT Score", 25),
                    ("Maxed AFT", 30),
                    ("Ran marathon", 30),
                    ("Reach 1000 lb Club", 30),
                    ("Dunked on the Supe + Ratio", 1000)
                ]

                cursor.executemany(
                    "INSERT INTO activities (name, coin_value) VALUES (%s, %s)",
                    default_activities
                )

            conn.commit()
            cursor.close()
            conn.close()

            print("Connected to MySQL and initialized database.")
            return

        except mysql.connector.Error as error:
            last_error = error
            print(f"MySQL not ready yet. Attempt {attempt + 1}/30: {error}")
            time.sleep(2)


    raise RuntimeError(f"Could not connect to MySQL after retries: {last_error}")

def get_db():
    return pool.get_connection()


def require_login():
    return session.get("user_id")


@app.route("/")
def home():
    if session.get("user_id"):
        return redirect("/dashboard.html")

    return redirect("/login.html")


@app.route("/login.html")
def login_page():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CadetCoin Login</title>

  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
    }

    body {
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      background: linear-gradient(135deg, #1f2937, #111827);
      color: #fff;
    }

    .login-container {
      background: #ffffff;
      color: #222;
      width: 100%;
      max-width: 400px;
      padding: 40px 30px;
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }

    .login-container h1 {
      text-align: center;
      margin-bottom: 10px;
      color: #111827;
    }

    .login-container p.subtitle {
      text-align: center;
      margin-bottom: 25px;
      color: #6b7280;
      font-size: 14px;
    }

    form {
      display: flex;
      flex-direction: column;
    }

    label {
      margin-bottom: 6px;
      font-weight: bold;
      font-size: 14px;
    }

    input {
      padding: 12px;
      margin-bottom: 18px;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      font-size: 14px;
      transition: border 0.2s ease, box-shadow 0.2s ease;
    }

    input:focus {
      outline: none;
      border-color: #2563eb;
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
    }

    button {
      background: #2563eb;
      color: white;
      border: none;
      padding: 12px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: bold;
      cursor: pointer;
      transition: background 0.2s ease, transform 0.1s ease;
    }

    button:hover {
      background: #1d4ed8;
    }

    button:active {
      transform: scale(0.98);
    }

    #errorMessage {
      margin-top: 15px;
      text-align: center;
      color: #dc2626;
      font-size: 14px;
      min-height: 20px;
    }

    .brand {
      text-align: center;
      font-size: 28px;
      font-weight: bold;
      color: #10b981;
      margin-bottom: 5px;
    }
  </style>
</head>

<body>
  <div class="login-container">
    <div class="brand">CadetCoin</div>
    <h1>Login</h1>
    <p class="subtitle">For help, contact MAJ Haskins at joshua.haskins2@westpoint.edu</p>

    <form id="loginForm">
      <label for="username">Username</label>
      <input id="username" type="text" placeholder="firstname.lastname" required>

      <label for="password">Password</label>
      <input id="password" type="password" placeholder="Enter your assigned ID" required>

      <button type="submit">Login</button>
    </form>

    <p id="errorMessage"></p>
  </div>

  <script>
    document.getElementById("loginForm").addEventListener("submit", async function (event) {
      event.preventDefault();

      const username = document.getElementById("username").value.trim();
      const password = document.getElementById("password").value.trim();

      const response = await fetch("/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({
          username: username,
          password: password
        })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        window.location.href = "/dashboard.html";
      } else {
        document.getElementById("errorMessage").textContent =
          result.error || "Login failed";
      }
    });
  </script>
</body>
</html>
""")






@app.route("/dashboard.html")
def dashboard_page():
    if not session.get("user_id"):
        return redirect("/login.html")

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CadetCoin Dashboard</title>

  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 0;
      background: #f4f4f4;
    }

    header {
      background: #222;
      color: white;
      padding: 20px;
      text-align: center;
    }

    nav {
      background: #444;
      padding: 10px;
      text-align: center;
    }

    nav a,
    nav button {
      color: white;
      margin: 0 15px;
      text-decoration: none;
      background: none;
      border: none;
      cursor: pointer;
      font-size: 16px;
    }

    section {
      background: white;
      margin: 20px auto;
      padding: 20px;
      width: 80%;
      max-width: 800px;
      border-radius: 8px;
    }

    button {
      background: #222;
      color: white;
      padding: 10px 15px;
      border: none;
      cursor: pointer;
      border-radius: 4px;
    }

    input,
    select {
      padding: 8px;
      margin: 5px 0 12px;
      width: 100%;
      box-sizing: border-box;
    }

    .coins {
      font-size: 24px;
      font-weight: bold;
      color: green;
    }

    .message {
      font-weight: bold;
      margin-top: 10px;
    }

    .success {
      color: green;
    }

    .error {
      color: #dc2626;
    }
  </style>
</head>

<body>
  <header>
    <h1>CadetCoin</h1>
    <p>Earn coins by staying physically active</p>
  </header>

  <nav>
    <a href="#dashboard">Dashboard</a>
    <a href="#workout">Log Workout</a>
    <a href="#leaderboard">Leaderboard</a>
    <a href="#rewards">Rewards</a>
    <a href="#admin">Admin</a>
    <button onclick="logout()">Logout</button>
  </nav>

  <section id="dashboard">
    <h2>Cadet Dashboard</h2>
    <p>Welcome, <span id="cadetName">Cadet</span>!</p>
    <p>Your Balance:</p>
    <p class="coins" id="coinBalance">0 CadetCoins</p>
  </section>

  <section id="workout">
    <h2>Log Workout</h2>

    <label>Workout Type</label>
    <select id="workoutType"></select>

    <label>Workout Notes</label>
    <input type="text" id="notes" placeholder="Example: Ran 3 miles">

    <button onclick="logWorkout()">Submit Workout</button>
    <p class="message" id="workoutMessage"></p>

    <h3>Workout History</h3>
    <ul id="history"></ul>
  </section>

  <section id="leaderboard">
    <h2>Leaderboard</h2>
    <ol id="leaderboardList"></ol>
  </section>

  <section id="rewards">
    <h2>Rewards</h2>
    <ul>
      <li>Company Store Discount - 50 coins</li>
      <li>Peer Challenge Entry - 25 coins</li>
      <li>PMI Incentive - 100 coins</li>
      <li>Privilege Reward - 150 coins</li>
    </ul>
  </section>

  <section id="admin">
    <h2>Admin Panel</h2>
    <p>Admins can configure coin values, manage cadet accounts, and review activity reports.</p>

    <label>Activity Name</label>
    <input type="text" id="adminActivityName" placeholder="Example: 5-mile run">

    <label>Coin Value</label>
    <input type="number" id="adminCoinValue" placeholder="Example: 40">

    <button onclick="saveActivity()">Save Activity Value</button>
    <p class="message" id="adminMessage"></p>
  </section>

  <script>
    function setMessage(id, text, type) {
      const element = document.getElementById(id);
      element.textContent = text;
      element.className = "message";

      if (type) {
        element.classList.add(type);
      }
    }

    async function apiFetch(url, options = {}) {
      const response = await fetch(url, {
        ...options,
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(options.headers || {})
        }
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.error || "Request failed");
      }

      return data;
    }

    async function loadDashboard() {
      try {
        const data = await apiFetch("/api/dashboard");

        document.getElementById("cadetName").innerText = data.user.name;
        document.getElementById("coinBalance").innerText = data.user.coins + " CadetCoins";

        const workoutSelect = document.getElementById("workoutType");
        workoutSelect.innerHTML = "";

        data.activities.forEach(activity => {
          const option = document.createElement("option");
          option.value = activity.id;
          option.innerText = activity.name + " - " + activity.coin_value + " coins";
          workoutSelect.appendChild(option);
        });

        const history = document.getElementById("history");
        history.innerHTML = "";

        if (data.workouts.length === 0) {
          const item = document.createElement("li");
          item.innerText = "No workouts logged yet.";
          history.appendChild(item);
        } else {
          data.workouts.forEach(workout => {
            const item = document.createElement("li");
            const notes = workout.notes ? " - " + workout.notes : "";
            item.innerText = workout.activity_name + notes + " - +" + workout.coins_earned + " coins";
            history.appendChild(item);
          });
        }

        const leaderboard = document.getElementById("leaderboardList");
        leaderboard.innerHTML = "";

        data.leaderboard.forEach(user => {
          const item = document.createElement("li");
          item.innerText = user.name + " - " + user.coins + " coins";
          leaderboard.appendChild(item);
        });

      } catch (error) {
        window.location.href = "/login.html";
      }
    }

    async function logWorkout() {
      const activityId = document.getElementById("workoutType").value;
      const notes = document.getElementById("notes").value;

      try {
        const data = await apiFetch("/api/workouts", {
          method: "POST",
          body: JSON.stringify({
            activity_id: activityId,
            notes: notes
          })
        });

        document.getElementById("notes").value = "";
        setMessage("workoutMessage", "Workout logged. Earned " + data.coins_earned + " coins.", "success");
        loadDashboard();
      } catch (error) {
        setMessage("workoutMessage", error.message, "error");
      }
    }

    async function saveActivity() {
      const name = document.getElementById("adminActivityName").value;
      const coinValue = document.getElementById("adminCoinValue").value;

      try {
        await apiFetch("/api/admin/activity", {
          method: "POST",
          body: JSON.stringify({
            name: name,
            coin_value: coinValue
          })
        });

        document.getElementById("adminActivityName").value = "";
        document.getElementById("adminCoinValue").value = "";
        setMessage("adminMessage", "Activity saved.", "success");
        loadDashboard();
      } catch (error) {
        setMessage("adminMessage", error.message, "error");
      }
    }

    async function logout() {
      await apiFetch("/api/logout", {
        method: "POST"
      });

      window.location.href = "/login.html";
    }

    loadDashboard();
  </script>
</body>
</html>
""")


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({
            "success": False,
            "error": "Username and password are required"
        }), 400

    if username != LOGIN_USERNAME or password != LOGIN_PASSWORD:
        return jsonify({
            "success": False,
            "error": "Invalid username or password"
        }), 401

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, coins FROM users ORDER BY id LIMIT 1")
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (name, coins) VALUES (%s, %s)", ("Cadet", 0))
        conn.commit()

        user = {
            "id": cursor.lastrowid,
            "name": "Cadet",
            "coins": 0
        }

    session.permanent = True #issues with cookie expiring before
    session["user_id"] = user["id"]


    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "user": user
    })


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()

    return jsonify({
        "success": True
    })


@app.route("/api/dashboard")
def dashboard():
    user_id = require_login()

    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, coins FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        session.clear()
        return jsonify({"error": "User not found"}), 404

    cursor.execute("SELECT id, name, coin_value FROM activities ORDER BY id")
    activities = cursor.fetchall()

    cursor.execute("""
        SELECT 
            workouts.id,
            activities.name AS activity_name,
            workouts.notes,
            workouts.coins_earned,
            DATE_FORMAT(workouts.created_at, '%Y-%m-%d %H:%i:%s') AS created_at
        FROM workouts
        JOIN activities ON workouts.activity_id = activities.id
        WHERE workouts.user_id = %s
        ORDER BY workouts.created_at DESC
    """, (user_id,))
    workouts = cursor.fetchall()

    cursor.execute("SELECT name, coins FROM users ORDER BY coins DESC")
    leaderboard = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "user": user,
        "activities": activities,
        "workouts": workouts,
        "leaderboard": leaderboard
    })


@app.route("/api/workouts", methods=["POST"])
def create_workout():
    user_id = require_login()

    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json() or {}

    activity_id = data.get("activity_id")
    notes = data.get("notes", "")

    if not activity_id:
        return jsonify({"error": "Activity ID is required"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, coin_value FROM activities WHERE id = %s", (activity_id,))
    activity = cursor.fetchone()

    if not activity:
        cursor.close()
        conn.close()
        return jsonify({"error": "Invalid activity"}), 400

    coins_earned = activity["coin_value"]

    cursor.execute("""
        INSERT INTO workouts (user_id, activity_id, notes, coins_earned)
        VALUES (%s, %s, %s, %s)
    """, (user_id, activity_id, notes, coins_earned))

    cursor.execute("""
        UPDATE users
        SET coins = coins + %s
        WHERE id = %s
    """, (coins_earned, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "message": "Workout logged",
        "coins_earned": coins_earned
    })


@app.route("/api/admin/activity", methods=["POST"])
def save_activity():
    user_id = require_login()

    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    coin_value = data.get("coin_value")

    if not name or not coin_value:
        return jsonify({"error": "Activity name and coin value are required"}), 400

    try:
        coin_value = int(coin_value)
    except ValueError:
        return jsonify({"error": "Coin value must be a number"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO activities (name, coin_value)
        VALUES (%s, %s)
    """, (name, coin_value))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "message": "Activity saved"
    })


init_database()

application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)