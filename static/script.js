// Where to send people once they're logged in.
// Swap this for your real dashboard route when it exists.
const POST_LOGIN_REDIRECT = "/docs";

const panels = {
  login: document.getElementById("login-panel"),
  register: document.getElementById("register-panel"),
  forgot: document.getElementById("forgot-panel"),
  reset: document.getElementById("reset-panel")
};

function showPanel(name) {
  Object.values(panels).forEach((el) => { el.hidden = true; });
  panels[name].hidden = false;
}

// ---------- panel switching ----------

document.getElementById("show-register").addEventListener("click", (e) => {
  e.preventDefault();
  showPanel("register");
});

document.getElementById("show-login").addEventListener("click", (e) => {
  e.preventDefault();
  showPanel("login");
});

document.getElementById("forgot-link").addEventListener("click", (e) => {
  e.preventDefault();
  showPanel("forgot");
});

document.getElementById("show-login-from-forgot").addEventListener("click", (e) => {
  e.preventDefault();
  showPanel("login");
});

document.getElementById("show-login-from-reset").addEventListener("click", (e) => {
  e.preventDefault();
  showPanel("login");
});

document.getElementById("show-reset-from-forgot").addEventListener("click", (e) => {
  e.preventDefault();
  showPanel("reset");
});

// ---------- show/hide password (works across all forms) ----------

document.querySelectorAll(".toggle-pw").forEach((btn) => {
  btn.addEventListener("click", () => {
    const input = document.getElementById(btn.dataset.target);
    const isHidden = input.type === "password";
    input.type = isHidden ? "text" : "password";
    btn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
  });
});

// ---------- helpers ----------

function setMessage(el, text) {
  el.textContent = text;
  el.classList.toggle("visible", Boolean(text));
}

async function postJSON(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(body)
  });
  const data = await response.json().catch(() => ({}));
  return { ok: response.ok, status: response.status, data };
}

// ---------- login ----------

const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");
const loginSubmit = document.getElementById("login-submit");

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage(loginError, "");

  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value;

  if (!username || !password) {
    setMessage(loginError, "Enter both your username and password.");
    return;
  }

  loginSubmit.disabled = true;
  loginSubmit.textContent = "Logging in…";

  try {
    const { ok, status, data } = await postJSON("/login", { username, password });

    if (!ok) {
      setMessage(loginError, status === 429
        ? "Too many attempts. Wait a minute and try again."
        : (data.detail || "Invalid username or password."));
      return;
    }

    window.location.href = POST_LOGIN_REDIRECT;

  } catch (err) {
    setMessage(loginError, "Couldn't reach the server. Check your connection and try again.");
  } finally {
    loginSubmit.disabled = false;
    loginSubmit.textContent = "Log in";
  }
});

// ---------- register ----------

const registerForm = document.getElementById("register-form");
const registerError = document.getElementById("register-error");
const registerSuccess = document.getElementById("register-success");
const registerSubmit = document.getElementById("register-submit");

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage(registerError, "");
  setMessage(registerSuccess, "");

  const username = document.getElementById("register-username").value.trim();
  const email = document.getElementById("register-email").value.trim();
  const password = document.getElementById("register-password").value;

  if (!username || !email || !password) {
    setMessage(registerError, "Fill in every field to continue.");
    return;
  }

  if (password.length < 8) {
    setMessage(registerError, "Password needs to be at least 8 characters.");
    return;
  }

  registerSubmit.disabled = true;
  registerSubmit.textContent = "Creating account…";

  try {
    const { ok, status, data } = await postJSON("/register", { username, email, password });

    if (!ok) {
      setMessage(registerError, status === 429
        ? "Too many attempts. Wait a minute and try again."
        : (data.detail || "Couldn't create that account."));
      return;
    }

    setMessage(registerSuccess, "Account created. You can log in now.");
    registerForm.reset();

    setTimeout(() => {
      showPanel("login");
      document.getElementById("login-username").value = username;
      document.getElementById("login-password").focus();
    }, 900);

  } catch (err) {
    setMessage(registerError, "Couldn't reach the server. Check your connection and try again.");
  } finally {
    registerSubmit.disabled = false;
    registerSubmit.textContent = "Create account";
  }
});

// ---------- forgot password ----------

const forgotForm = document.getElementById("forgot-form");
const forgotError = document.getElementById("forgot-error");
const forgotSuccess = document.getElementById("forgot-success");
const forgotDevNote = document.getElementById("forgot-dev-note");
const forgotSubmit = document.getElementById("forgot-submit");

forgotForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage(forgotError, "");
  setMessage(forgotSuccess, "");
  forgotDevNote.hidden = true;

  const email = document.getElementById("forgot-email").value.trim();

  if (!email) {
    setMessage(forgotError, "Enter the email on your account.");
    return;
  }

  forgotSubmit.disabled = true;
  forgotSubmit.textContent = "Sending…";

  try {
    const { ok, status, data } = await postJSON("/forgot-password", { email });

    if (!ok) {
      setMessage(forgotError, status === 429
        ? "Too many attempts. Wait a minute and try again."
        : (data.detail || "Something went wrong. Try again."));
      return;
    }

    setMessage(forgotSuccess, data.message || "If that email is registered, a reset link has been generated.");

    // Backend is running without a real email provider connected, so it
    // hands back the token directly for now — surface it so the flow is
    // testable. Once email sending is wired up server-side, this block
    // (and "reset_token" in the API response) goes away.
    if (data.reset_token) {
      forgotDevNote.innerHTML =
        "<strong>Dev mode — no email service connected</strong>" +
        "This token would normally be emailed to you:<br>" + data.reset_token;
      forgotDevNote.hidden = false;

      document.getElementById("reset-token").value = data.reset_token;
    }

  } catch (err) {
    setMessage(forgotError, "Couldn't reach the server. Check your connection and try again.");
  } finally {
    forgotSubmit.disabled = false;
    forgotSubmit.textContent = "Send reset link";
  }
});

// ---------- reset password ----------

const resetForm = document.getElementById("reset-form");
const resetError = document.getElementById("reset-error");
const resetSuccess = document.getElementById("reset-success");
const resetSubmit = document.getElementById("reset-submit");

resetForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage(resetError, "");
  setMessage(resetSuccess, "");

  const token = document.getElementById("reset-token").value.trim();
  const newPassword = document.getElementById("reset-password").value;

  if (!token || !newPassword) {
    setMessage(resetError, "Paste your reset token and choose a new password.");
    return;
  }

  if (newPassword.length < 8) {
    setMessage(resetError, "Password needs to be at least 8 characters.");
    return;
  }

  resetSubmit.disabled = true;
  resetSubmit.textContent = "Resetting…";

  try {
    const { ok, status, data } = await postJSON("/reset-password", {
      token,
      new_password: newPassword
    });

    if (!ok) {
      setMessage(resetError, status === 429
        ? "Too many attempts. Wait a minute and try again."
        : (data.detail || "Couldn't reset your password. The link may have expired."));
      return;
    }

    setMessage(resetSuccess, "Password updated. Redirecting to log in…");
    resetForm.reset();

    setTimeout(() => showPanel("login"), 1200);

  } catch (err) {
    setMessage(resetError, "Couldn't reach the server. Check your connection and try again.");
  } finally {
    resetSubmit.disabled = false;
    resetSubmit.textContent = "Reset password";
  }
});