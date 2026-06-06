import { ImageResponse } from "next/og";

export const runtime = "edge";

export async function GET() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "1200px",
          height: "630px",
          background: "linear-gradient(135deg, #1e40af 0%, #1d4ed8 50%, #0f172a 100%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "sans-serif",
          padding: "60px",
        }}
      >
        {/* Logo row */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "32px" }}>
          <div style={{
            width: "56px", height: "56px", background: "#60a5fa",
            borderRadius: "14px", display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "32px",
          }}>⚡</div>
          <span style={{ color: "#93c5fd", fontSize: "32px", fontWeight: "700", letterSpacing: "-1px" }}>
            Testura
          </span>
        </div>

        {/* Headline */}
        <div style={{
          color: "#ffffff", fontSize: "56px", fontWeight: "800",
          textAlign: "center", lineHeight: "1.15", marginBottom: "24px", letterSpacing: "-2px",
        }}>
          AI writes and runs tests
          <br />for your code.
        </div>

        {/* Sub */}
        <div style={{
          color: "#93c5fd", fontSize: "24px", textAlign: "center",
          maxWidth: "700px", lineHeight: "1.5",
        }}>
          Connect your GitHub repo — Testura generates tests, runs them, and tells you what broke.
        </div>

        {/* Stats row */}
        <div style={{
          display: "flex", gap: "40px", marginTop: "48px",
        }}>
          {[["84%", "Pass rate"], ["543+", "Tests run"], ["Free", "To start"]].map(([val, label]) => (
            <div key={label} style={{
              background: "rgba(255,255,255,0.1)", borderRadius: "16px",
              padding: "20px 36px", textAlign: "center",
            }}>
              <div style={{ color: "#fff", fontSize: "32px", fontWeight: "800" }}>{val}</div>
              <div style={{ color: "#93c5fd", fontSize: "16px", marginTop: "4px" }}>{label}</div>
            </div>
          ))}
        </div>

        {/* URL */}
        <div style={{ color: "#60a5fa", fontSize: "20px", marginTop: "40px", fontWeight: "600" }}>
          testura.dev
        </div>
      </div>
    ),
    { width: 1200, height: 630 }
  );
}
