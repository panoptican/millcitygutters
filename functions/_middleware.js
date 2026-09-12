const PRIVATE_PREFIXES = ["/.seo", "/.agents", "/.wrangler", "/.git", "/qa"];
const PRIVATE_FILES = ["/.gitignore", "/.assetsignore", "/.gitattributes"];

function isPrivate(pathname) {
  if (PRIVATE_FILES.includes(pathname)) return true;
  return PRIVATE_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(prefix + "/")
  );
}

export async function onRequest(context) {
  const { pathname } = new URL(context.request.url);
  if (!isPrivate(pathname)) return context.next();

  try {
    const res = await context.env.ASSETS.fetch(
      new URL("/404.html", context.request.url)
    );
    return new Response(res.body, {
      status: 404,
      headers: { "content-type": "text/html; charset=utf-8" },
    });
  } catch (err) {
    return new Response("Not Found", {
      status: 404,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }
}
