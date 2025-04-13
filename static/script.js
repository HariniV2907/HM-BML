document.getElementById("registrationForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const data = {
        name: document.getElementById("name").value,
        age: document.getElementById("age").value,
        email: document.getElementById("email").value,
        phone: document.getElementById("phone").value,
        designation: document.getElementById("designation").value,
        otp: document.getElementById("otp").value,
        password: document.getElementById("password").value
    };
    const res = await fetch("/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });
    const result = await res.json();
    document.getElementById("message").textContent = result.message;
    if (result.qrCode) {
        const qrImg = document.getElementById("qrCode");
        qrImg.src = result.qrCode;
        qrImg.style.display = "block";
    }
});

async function sendOTP() {
    const email = document.getElementById("email").value;
    if (!email) return alert("Enter email first");
    const res = await fetch("/send-otp", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ email })
    });
    const result = await res.json();
    document.getElementById("message").textContent = result.message;
}
