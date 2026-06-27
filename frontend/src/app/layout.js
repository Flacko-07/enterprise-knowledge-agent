import './globals.css';

export const metadata = {
  title: 'Enterprise Knowledge Assistant',
  description: 'AI-powered RAG system for enterprise document Q&A',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
