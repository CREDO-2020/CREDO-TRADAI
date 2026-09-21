const SUPABASE_URL = "https://vudmpeluukvraqozkwxr.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "REPLACE_WITH_SUPABASE_PUBLISHABLE_KEY";

let supabaseClient = null;

if (window.supabase && SUPABASE_PUBLISHABLE_KEY.startsWith("sb_")) {
  supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
}

async function signUp(email, password) {
  if (!supabaseClient) throw new Error("Supabase client is not configured.");
  const { data, error } = await supabaseClient.auth.signUp({ email, password });
  if (error) throw error;
  return data;
}

async function signIn(email, password) {
  if (!supabaseClient) throw new Error("Supabase client is not configured.");
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

async function cloudHeaders() {
  const user = await currentUser();
  if (!user) throw new Error("Please sign in first.");
  return { "X-User-ID": user.id };
}
