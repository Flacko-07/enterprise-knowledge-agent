import './globals.css';
import ChatInterface from '../components/ChatInterface';

export const metadata = {
  title: 'Enterprise Knowledge Assistant',
  description: 'Agentic RAG powered by Llama 3.2',
};

export default function Home() {
  return (
    <div className="h-screen flex flex-col relative bg-[var(--bg-main)]">
      {/* Abstract Background Grid/Gradients */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        {/* Top Left Gradient */}
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-indigo-600/5 blur-3xl"></div>
        {/* Bottom Right Gradient */}
        <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] rounded-full bg-purple-600/5 blur-3xl"></div>
        {/* Grid Pattern */}
        <div className="absolute inset-0 opacity-[0.02]" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)', backgroundSize: '60px 60px' }}></div>
      </div>

      <ChatInterface />
    </div>
  );
}