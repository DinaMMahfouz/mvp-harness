import type { SupabaseClient } from "@supabase/supabase-js";

/**
 * The Supabase JS client is loaded from the CDN (see index.html) as the
 * global `window.supabase`, not re-bundled from the npm package - that
 * package is a dev dependency here purely for TypeScript types, so there is
 * exactly one copy of the client library on the page. `createClient` below
 * is the CDN global's own function; only its *type* comes from npm.
 */
declare global {
  interface Window {
    supabase: {
      createClient: typeof import("@supabase/supabase-js").createClient;
    };
  }
}

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!url || !anonKey) {
  // Fail loudly at startup rather than producing confusing "fetch failed"
  // errors deep inside a component the first time someone signs in.
  throw new Error(
    "VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY must be set (see frontend/.env.example)."
  );
}

export const supabase: SupabaseClient = window.supabase.createClient(url, anonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});
