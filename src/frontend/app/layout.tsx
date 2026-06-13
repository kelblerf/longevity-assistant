import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Longevity-assistant",
  description:
    "Chat-first osobni AI radce pro longevity, rytmus, dech, regeneraci a personalizovane vedeni dne.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="cs">
      <body>{children}</body>
    </html>
  );
}

