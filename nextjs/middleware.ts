import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";
import { allowedRoutes } from "@/consts";

export default auth((req) => {
  // If not authenticated, redirect to login page (except for /login and /signup)
  if (!req.auth) {
    // Import allowedRoutes from consts
    // (already imported at the top)
    if (!allowedRoutes.includes(req.nextUrl.pathname)) {
      const loginUrl = new URL("/login", req.url);
      loginUrl.searchParams.set("callbackUrl", req.url);
      return NextResponse.redirect(loginUrl);
    }
  }
  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
