


document.getElementById("loginForm").addEventListener("submit", async function (event) {
  event.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

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