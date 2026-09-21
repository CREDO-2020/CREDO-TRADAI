const SUPABASE_URL = "https://vudmpeluukvraqozkwxr.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "sb_publishable_U19_dtCpAZ3tJTooca7M-Q_nNSYL1bl";

let supabaseClient = null;

if (window.supabase) {
  supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
}

async function signUp(email, password) {
  if (!supabaseClient) throw new Error("Supabase client is not available.");
  const { data, error } = await supabaseClient.auth.signUp({ email, password });
  if (error) throw error;
  return data;
}

async function signIn(email, password) {
  if (!supabaseClient) throw new Error("Supabase client is not available.");
  const { data, error } = await supabaseClient.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

async function signOut() {
  if (!supabaseClient) return;
  const { error } = await supabaseClient.auth.signOut();
  if (error) throw error;
}

async function currentUser() {
  if (!supabaseClient) return null;
  const { data, error } = await supabaseClient.auth.getUser();
  if (error) return null;
  return data.user;
}

async function accessToken() {
  if (!supabaseClient) return null;
  const { data: { session } } = await supabaseClient.auth.getSession();
  return session?.access_token || null;
}

async function authFetch(url, options = {}) {
  const token = await accessToken();
  if (!token) {
    window.location.href = "/login";
    throw new Error("Authentication required.");
  }
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", "Bearer " + token);
  return fetch(url, { ...options, headers });
}
