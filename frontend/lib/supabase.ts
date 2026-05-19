import { createClient, SupabaseClient } from "@supabase/supabase-js";

let _client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (!_client) {
    _client = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
  }
  return _client;
}

// Convenience alias used across the app
export const supabase = {
  auth: {
    getSession: () => getSupabase().auth.getSession(),
    signInWithOAuth: (opts: Parameters<SupabaseClient["auth"]["signInWithOAuth"]>[0]) =>
      getSupabase().auth.signInWithOAuth(opts),
    signOut: () => getSupabase().auth.signOut(),
  },
  table: (name: string) => getSupabase().from(name),
};

export async function getSession() {
  const { data } = await supabase.auth.getSession();
  return data.session;
}

export async function signInWithGitHub() {
  return supabase.auth.signInWithOAuth({
    provider: "github",
    options: {
      scopes: "repo read:user",
      redirectTo: `${window.location.origin}/dashboard`,
    },
  });
}

export async function signOut() {
  return supabase.auth.signOut();
}
