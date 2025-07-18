document.addEventListener("DOMContentLoaded", function () {
  const jsonForm = document.getElementById("jsonForm");
  const jsonData = document.getElementById("jsonData");
  const messageDiv = document.getElementById("message");
  const aliasButtons = document.getElementById("aliasButtons");

  // Load current JSON
  fetch("/get_data")
    .then((res) => res.json())
    .then((data) => {
      jsonData.value = JSON.stringify(data, null, 2);

      if (data.aliases) {
        Object.keys(data.aliases).forEach((alias) => {
          const btn = document.createElement("button");
          btn.classList.add("btn", "secondary");
          btn.textContent = alias;
          btn.onclick = () => {
            alert(`Alias '${alias}' maps to '${data.aliases[alias]}'`);
          };
          aliasButtons.appendChild(btn);
        });
      }
    });

  // Save handler
  jsonForm.addEventListener("submit", function (e) {
    e.preventDefault();
    try {
      const parsed = JSON.parse(jsonData.value);
      fetch("/save_data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed),
      })
        .then((res) => res.json())
        .then((res) => {
          if (res.status === "success") {
            messageDiv.innerText = "✅ Data saved successfully!";
            messageDiv.style.color = "#00ff99";
          } else {
            messageDiv.innerText = "❌ Error: " + res.message;
            messageDiv.style.color = "#ff4444";
          }
        });
    } catch (err) {
      messageDiv.innerText = "❌ Invalid JSON!";
      messageDiv.style.color = "#ff4444";
    }
  });

  // Add Admin Modal
  const addAdminBtn = document.getElementById("addAdminBtn");
  const addAdminModal = document.getElementById("addAdminModal");
  const addAdminForm = document.getElementById("addAdminForm");

  if (addAdminBtn) {
    addAdminBtn.onclick = () => {
      addAdminModal.style.display = "block";
    };
  }

  if (addAdminForm) {
    addAdminForm.onsubmit = function (e) {
      e.preventDefault();
      const username = document.getElementById("newAdminUser").value.trim();
      const password = document.getElementById("newAdminPass").value.trim();

      fetch("/add_admin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      })
        .then((res) => res.json())
        .then((res) => {
          if (res.status === "success") {
            alert("✅ New admin added.");
            addAdminForm.reset();
            addAdminModal.style.display = "none";
          } else {
            alert("❌ Error: " + res.message);
          }
        });
    };
  }
});


// Add alias to textarea when alias button is clicked
function insertAlias(aliasKey) {
  const textarea = document.getElementById("json-input");
  const textToAdd = `\n\n"${aliasKey}": "..."`;
  textarea.value += textToAdd;
  textarea.focus();
}
