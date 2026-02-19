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

  const toEmail = context.env.CONTACT_EMAIL || "info@millcitygutters.com";
  const fromEmail = context.env.CONTACT_FROM_EMAIL || "noreply@millcitygutters.com";

  const mailChannelsResponse = await fetch("https://api.mailchannels.net/tx/v1/send", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      personalizations: [{ to: [{ email: toEmail, name: "Mill City Gutters" }] }],
      from: { email: fromEmail, name: "Mill City Gutters Website" },
      reply_to: { email, name },
      subject: "New message from millcitygutters.com",
      content: [
        {
          type: "text/plain",
          value: `Name: ${name}\nEmail: ${email}\n\nMessage:\n${message}`
        }
      ]
    })
  });

  if (!mailChannelsResponse.ok) {
    return jsonResponse({ error: "Unable to send email right now" }, 502);
  }

  return jsonResponse({ ok: true });
}
