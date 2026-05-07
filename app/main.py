# USed Chat: 


from flask import Flask, jsonify, request, render_template_string
import mysql.connector
from mysql.connector import pooling
import os

app = Flask(__name__)

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "cadetcoin")

pool = None


def init_database():
    global pool

    server_conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    server_cursor = server_conn.cursor()
    server_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
    server_cursor.close()
    server_conn.close()

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
        cursor.execute("INSERT INTO users (name, coins) VALUES (%s, %s)", ("Cadet", 0))

    cursor.execute("SELECT COUNT(*) FROM activities")
    if cursor.fetchone()[0] == 0:
        default_activities = [
            ("Run", 10),
            ("Gym Workout", 15),
            ("Improved AFT Score", 25),
            ("Fitness Milestone", 30)
        ]
        cursor.executemany(
            "INSERT INTO activities (name, coin_value) VALUES (%s, %s)",
            default_activities
        )

    conn.commit()
    cursor.close()
    conn.close()


def get_db():
    return pool.get_connection()


@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
  <title>CadetCoin</title>
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

    nav a {
      color: white;
      margin: 0 15px;
      text-decoration: none;
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
    }

    input, select {
      padding: 8px;
      margin: 5px 0;
      width: 100%;
      box-sizing: border-box;
    }

    .coins {
      font-size: 24px;
      font-weight: bold;
      color: green;
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
  </section>

  <script>
    async function loadDashboard() {
      const response = await fetch("/api/dashboard");
      const data = await response.json();

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

      data.workouts.forEach(workout => {
        const item = document.createElement("li");
        item.innerText = workout.activity_name + " - " + workout.notes + " - +" + workout.coins_earned + " coins";
        history.appendChild(item);
      });

      const leaderboard = document.getElementById("leaderboardList");
      leaderboard.innerHTML = "";

      data.leaderboard.forEach(user => {
        const item = document.createElement("li");
        item.innerText = user.name + " - " + user.coins + " coins";
        leaderboard.appendChild(item);
      });
    }

    async function logWorkout() {
      const activityId = document.getElementById("workoutType").value;
      const notes = document.getElementById("notes").value;

      const response = await fetch("/api/workouts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          activity_id: activityId,
          notes: notes
        })
      });

      if (!response.ok) {
        alert("Error logging workout.");
        return;
      }

      document.getElementById("notes").value = "";
      loadDashboard();
    }

    async function saveActivity() {
      const name = document.getElementById("adminActivityName").value;
      const coinValue = document.getElementById("adminCoinValue").value;

      const response = await fetch("/api/admin/activity", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: name,
          coin_value: coinValue
        })
      });

      if (!response.ok) {
        alert("Error saving activity.");
        return;
      }

      document.getElementById("adminActivityName").value = "";
      document.getElementById("adminCoinValue").value = "";
      loadDashboard();
    }

    loadDashboard();
  </script>

</body>
</html>
""")


@app.route("/api/dashboard")
def dashboard():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, coins FROM users WHERE id = %s", (1,))
    user = cursor.fetchone()

    cursor.execute("SELECT id, name, coin_value FROM activities ORDER BY id")
    activities = cursor.fetchall()

    cursor.execute("""
        SELECT 
            workouts.id,
            activities.name AS activity_name,
            workouts.notes,
            workouts.coins_earned,
            workouts.created_at
        FROM workouts
        JOIN activities ON workouts.activity_id = activities.id
        WHERE workouts.user_id = %s
        ORDER BY workouts.created_at DESC
    """, (1,))
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
    data = request.get_json()

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
    """, (1, activity_id, notes, coins_earned))

    cursor.execute("""
        UPDATE users
        SET coins = coins + %s
        WHERE id = %s
    """, (coins_earned, 1))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Workout logged", "coins_earned": coins_earned})


@app.route("/api/admin/activity", methods=["POST"])
def save_activity():
    data = request.get_json()

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

    return jsonify({"message": "Activity saved"})


init_database()

# Apache mod_wsgi looks for "application"
application = app

if __name__ == "__main__":
    app.run(debug=True)