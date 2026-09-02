import { useEffect, useState } from "react";

const SCRIPT = "https://accounts.google.com/gsi/client";
const BUSY = new Set(["loading", "waiting", "signing-in", "success"]);

export default function GoogleCrewSignIn({ config, configLoaded }) {
  const [state, setState] = useState("loading");
  const [message, setMessage] = useState("Preparing secure Google sign-in…");

  useEffect(() => {
    if (!configLoaded) return;
    if (config?.provider !== "google" || !config.google_client_id) return;
    let active = true;
    const initialize = () => {
      if (!active || !window.google?.accounts?.id) return;
      window.google.accounts.id.initialize({
        client_id: config.google_client_id,
        callback: async ({ credential }) => {
          if (!credential) {
            setState("error");
            setMessage("Google did not return an identity credential. Please try again.");
            return;
          }
          setState("signing-in");
          setMessage("Resolving your authenticated crew identity…");
          try {
            const response = await fetch("/api/auth/google", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ credential }),
            });
            if (!response.ok) {
              const payload = await response.json().catch(() => ({}));
              throw new Error(typeof payload.detail === "string" ? payload.detail : "Google account is not assigned to this production.");
            }
            setState("success");
            setMessage("Identity confirmed. Entering the production…");
            window.setTimeout(() => window.location.reload(), 500);
          } catch (error) {
            setState("error");
            setMessage(error.message || "Google sign-in failed. Please try again.");
          }
        },
      });
      setState("ready");
      setMessage("Your role and authority will be resolved securely after Google verifies your identity.");
    };
    if (window.google?.accounts?.id) {
      initialize();
      return () => { active = false; };
    }
    const existing = document.querySelector('script[src="' + SCRIPT + '"]');
    const script = existing || document.createElement("script");
    const unavailable = () => {
      if (!active) return;
      setState("unavailable");
      setMessage("Google sign-in is temporarily unavailable because the secure sign-in service could not load.");
    };
    script.addEventListener("load", initialize);
    script.addEventListener("error", unavailable);
    if (!existing) {
      script.src = SCRIPT;
      script.async = true;
      document.head.appendChild(script);
    }
    return () => {
      active = false;
      script.removeEventListener("load", initialize);
      script.removeEventListener("error", unavailable);
    };
  }, [config, configLoaded]);

  const continueWithGoogle = () => {
    if (!["ready", "error"].includes(state) || !window.google?.accounts?.id) return;
    setState("waiting");
    setMessage("Choose the Google account assigned to this production.");
    window.google.accounts.id.prompt((notice) => {
      if (notice.isNotDisplayed?.() || notice.isSkippedMoment?.()) {
        setState("error");
        setMessage("Google could not open the account chooser. Check browser sign-in permissions and try again.");
      }
    });
  };

  const unavailable = configLoaded && (config?.provider !== "google" || !config.google_client_id);
  const displayState = unavailable ? "unavailable" : state;
  const displayMessage = unavailable ? "Google sign-in is temporarily unavailable. The production administrator must restore OAuth configuration." : message;
  const busy = BUSY.has(displayState);
  const label = displayState === "success" ? "Identity confirmed" : busy ? "Connecting to Google…" : "Continue with Google";
  return (
    <div className="sign-in-action">
      <button type="button" className="google-sign-in-cta" onClick={continueWithGoogle}
        disabled={!["ready", "error"].includes(displayState)} aria-describedby="google-sign-in-status" aria-busy={busy}>
        {label}
      </button>
      <p id="google-sign-in-status" className={"auth-status " + displayState}
        role={displayState === "error" || displayState === "unavailable" ? "alert" : "status"}>{displayMessage}</p>
    </div>
  );
}
