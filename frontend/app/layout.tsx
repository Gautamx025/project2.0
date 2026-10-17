import type { Metadata } from 'next';
import '@fontsource/fraunces/400.css';
import '@fontsource/fraunces/500.css';
import '@fontsource/dm-sans/400.css';
import '@fontsource/dm-sans/500.css';
import '@fontsource/dm-sans/600.css';
import '@fontsource/jetbrains-mono/400.css';
import './globals.css';
export const metadata: Metadata = { title: 'Snap-2-Store — The catalog darkroom', description: 'From your shop counter to a store-ready product draft. Built for independent sellers by NeuralShift.' };
export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body>{children}</body></html>;
}
