async function sendOtp() {
  const email = document.getElementById('email').value;
  const res = await fetch('/send_otp', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({email})
  });
  const data = await res.json();
  if (data.status === 'otp_sent') {
    showMsg('OTP sent to your email.');
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'block';
  } else {
    showMsg(data.error);
  }
}

async function verifyOtp() {
  const email = document.getElementById('email').value;
  const otp = document.getElementById('otp').value;
  const res = await fetch('/verify_otp', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({email, otp})
  });
  const data = await res.json();
  if (data.status === 'verified' || data.status === 'already_verified') {
    showMsg('Verified! Now enter your phone.');
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step3').style.display = 'block';
  } else {
    showMsg(data.error);
  }
}

async function savePhone() {
  const phone = document.getElementById('phone').value;
  const res = await fetch('/save_phone', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({phone})
  });
  const data = await res.json();
  if (data.status === 'phone_saved') {
    window.location = '/dashboard';
  } else showMsg(data.error);
}

function showMsg(msg) {
  document.getElementById('message').innerText = msg;
    }
