const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store"
    }
  });
}

export async function onRequestPost(context) {
  let payload;

  try {
    payload = await context.request.json();
  } catch {
    return jsonResponse({ error: "Invalid JSON payload" }, 400);
  }

  const name = String(payload?.name || "").trim();
  const email = String(payload?.email || "").trim();
  const message = String(payload?.message || "").trim();

  if (!name || !email || !message) {
    return jsonResponse({ error: "Name, email, and message are required" }, 400);
  }

  if (!EMAIL_REGEX.test(email)) {
    return jsonResponse({ error: "Email is invalid" }, 400);
  }

  const apiKey = context.env.RESEND_API_KEY;
  if (!apiKey) {
    return jsonResponse({ error: "Email service not configured" }, 503);
  }

  const toEmail = context.env.CONTACT_EMAIL || "info@millcitygutters.com";
  const fromEmail = context.env.CONTACT_FROM_EMAIL || "website@millcitygutters.com";

  const resendResponse = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      from: `Mill City Gutters Website <${fromEmail}>`,
      to: [toEmail],
      reply_to: `${name} <${email}>`,
      subject: "New message from millcitygutters.com",
      text: `Name: ${name}\nEmail: ${email}\n\nMessage:\n${message}`
    })
  });

  if (!resendResponse.ok) {
    return jsonResponse({ error: "Unable to send email right now" }, 502);
  }

  return jsonResponse({ ok: true });
}
