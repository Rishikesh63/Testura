import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

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
