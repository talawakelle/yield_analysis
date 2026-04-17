import "./globals.css";

export const metadata = {
  title: "Plantation Yield Intelligence",
  description: "Modern plantation yield dashboard and admin data input suite",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
