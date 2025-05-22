"use client";
import { Suspense, useState, useEffect } from "react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useForm } from "react-hook-form";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
  FormField,
} from "@/components/ui/form";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Show alert dialog on login error
  useEffect(() => {
    const errorParam = searchParams.get("error");
    if (errorParam) {
      alert("Login failed: Invalid email or password.");
    }
  }, [searchParams]);

  // Toast state for logout success
  const [showLogoutToast, setShowLogoutToast] = useState(false);
  useEffect(() => {
    const logoutParam = searchParams.get("logout");
    if (logoutParam === "success") {
      setShowLogoutToast(true);
      const timer = setTimeout(() => setShowLogoutToast(false), 4000);
      return () => clearTimeout(timer);
    }
  }, [searchParams]);

  const form = useForm({
    defaultValues: {
      email: "",
      password: "",
    },
  });

  async function onSubmit(values: { email: string; password: string }) {
    setLoading(true);
    setError("");
    const res = await signIn("credentials", {
      ...values,
      redirect: false,
    });
    setLoading(false);
    if (res?.ok) {
      router.push("/");
    } else {
      setError(res?.error || "Invalid credentials");
    }
  }

  return (
    <>
      <Dialog open={showLogoutToast} onOpenChange={setShowLogoutToast}>
        <DialogContent className="max-w-xs p-4 flex flex-row items-center gap-2 bg-green-50 border-green-300 shadow-lg">
          <DialogTitle className="sr-only">Logout Success</DialogTitle>
          <span className="text-green-900 font-medium">You have been logged out successfully.</span>
        </DialogContent>
      </Dialog>
      <div className="flex min-h-screen items-center justify-center">
        <Form {...form}>
          <form
            className="bg-white p-8 rounded-lg shadow-md w-full max-w-md"
            onSubmit={form.handleSubmit(onSubmit)}
          >
            <h1 className="text-2xl font-bold mb-6">Login</h1>

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem className="mb-4">
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" {...field} required />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem className="mb-6">
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input type="password" {...field} required />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </Button>

            <Button
              type="button"
              variant="secondary"
              className="w-full mt-4" // Added mt-4 for spacing
              onClick={() => signIn("github")}
            >
              Sign in with GitHub
            </Button>
          </form>
        </Form>
      </div>
    </>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Loading page details...</div>}> 
      <LoginContent />
    </Suspense>
  );
}
