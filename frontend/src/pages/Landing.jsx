import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import GalaxyAnimation from '../components/GalaxyAnimation';

const Landing = () => {
  const canvasRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    
    let width = window.innerWidth;
    let height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
    
    let particles = [];
    const numParticles = 25; // Drastically reduced for performance
    
    class Particle {
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 1.5;
        this.vy = (Math.random() - 0.5) * 1.5;
        this.radius = Math.random() * 1.5 + 0.5;
      }
      
      update() {
        this.x += this.vx;
        this.y += this.vy;
        
        if (this.x < 0 || this.x > width) this.vx = -this.vx;
        if (this.y < 0 || this.y > height) this.vy = -this.vy;
      }
      
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(99, 102, 241, 0.6)';
        ctx.fill();
      }
    }
    
    for (let i = 0; i < numParticles; i++) {
      particles.push(new Particle());
    }
    
    let mouse = { x: null, y: null };
    
    const handleMouseMove = (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };
    
    const handleMouseLeave = () => {
      mouse.x = null;
      mouse.y = null;
    };
    
    const handleResize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);
    window.addEventListener('resize', handleResize);
    
    const drawLines = () => {
      for (let i = 0; i < numParticles; i++) {
        for (let j = i + 1; j < numParticles; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          
          if (dist < 150) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(99, 102, 241, ${1 - dist / 150})`;
            ctx.lineWidth = 0.8;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
        
        // Connect to mouse hover for interaction
        if (mouse.x !== null && mouse.y !== null) {
          const dx = particles[i].x - mouse.x;
          const dy = particles[i].y - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          
          if (dist < 200) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(168, 85, 247, ${1 - dist / 200})`; // Purple glow near mouse
            ctx.lineWidth = 1.2;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.stroke();
          }
        }
      }
    };
    
    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      
      particles.forEach(p => {
        p.update();
        p.draw();
      });
      
      drawLines();
      animationFrameId = requestAnimationFrame(animate);
    };
    
    animate();
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div style={{ position: 'relative', minHeight: '100vh', overflow: 'hidden', backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)' }}>
      {/* Interactive Background Canvas */}
      <canvas 
        ref={canvasRef} 
        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0, pointerEvents: 'none' }}
      />
      
      {/* Content */}
      <div style={{ position: 'relative', zIndex: 1, height: '100vh', overflowY: 'auto' }}>
        
        {/* Navigation Navbar */}
        <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.5rem 5%', backdropFilter: 'blur(10px)', borderBottom: '1px solid rgba(255,255,255,0.05)', position: 'sticky', top: 0, zIndex: 50 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', cursor: 'pointer' }}>
            <div className="logo-icon" style={{ width: '40px', height: '40px', fontSize: '1.2rem', margin: 0 }}>R</div>
            <span style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-display)', letterSpacing: '1px' }}>RAGaaS</span>
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button className="btn btn-secondary" onClick={() => navigate('/auth')}>Sign In</button>
            <button className="btn btn-primary" onClick={() => navigate('/auth')}>Start for Free</button>
          </div>
        </nav>

        {/* Hero Banner */}
        <main style={{ padding: '8rem 5% 5rem', display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', maxWidth: '1400px', margin: '0 auto', gap: '2rem', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 450px', textAlign: 'left', zIndex: 10 }}>
            <h1 className="animate-fade-in" style={{ fontSize: '4.5rem', fontFamily: 'var(--font-display)', fontWeight: 700, lineHeight: 1.1, marginBottom: '1.5rem' }}>
              Build <span style={{ background: 'var(--accent-glow)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Agentic RAG</span> in Minutes
            </h1>
            <p className="animate-fade-in" style={{ fontSize: '1.25rem', color: 'var(--text-secondary)', marginBottom: '3rem', animationDelay: '0.1s', animationFillMode: 'both', lineHeight: 1.6 }}>
              Deploy production-ready retrieval systems over your proprietary data. Seamlessly scale from a free local prototype to a multi-modal enterprise architecture.
            </p>
            <div className="animate-fade-in" style={{ display: 'flex', gap: '1.5rem', animationDelay: '0.2s', animationFillMode: 'both' }}>
              <button className="btn btn-primary" style={{ padding: '1rem 2.5rem', fontSize: '1.1rem' }} onClick={() => navigate('/auth')}>Start Building</button>
              <button className="btn btn-secondary" style={{ padding: '1rem 2.5rem', fontSize: '1.1rem' }} onClick={() => document.getElementById('how-it-works').scrollIntoView({ behavior: 'smooth' })}>How it Works</button>
            </div>
          </div>
          
          {/* Galaxy Canvas Visualization */}
          <div className="animate-fade-in" style={{ flex: '1 1 650px', display: 'flex', justifyContent: 'center', animationDelay: '0.3s', animationFillMode: 'both' }}>
            <GalaxyAnimation />
          </div>
        </main>

        {/* How to Use Section */}
        <section id="how-it-works" style={{ padding: '5rem 5%', background: 'linear-gradient(to bottom, transparent, rgba(18,18,29,0.8))' }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
              <h2 style={{ fontSize: '2.5rem', fontFamily: 'var(--font-display)', marginBottom: '1rem' }}>How to Use the System</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>Deploy an advanced AI assistant tailored to your data in three simple steps.</p>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
              
              <div className="glass-card" style={{ textAlign: 'center', padding: '3rem 2rem', transition: 'transform 0.3s' }}>
                <div style={{ width: '60px', height: '60px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem auto', color: 'var(--accent-primary)', fontSize: '1.5rem', fontWeight: 'bold' }}>1</div>
                <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', fontFamily: 'var(--font-display)' }}>Upload Data</h3>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>Create a namespace and securely ingest your PDFs, Word documents, and TXT files. We automatically chunk, embed, and store them in a high-performance vector database.</p>
              </div>
              
              <div className="glass-card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
                <div style={{ width: '60px', height: '60px', background: 'rgba(168, 85, 247, 0.1)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem auto', color: 'var(--accent-secondary)', fontSize: '1.5rem', fontWeight: 'bold' }}>2</div>
                <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', fontFamily: 'var(--font-display)' }}>Configure Pipeline</h3>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>Choose between Standard RAG, Cache-Augmented Generation (CAG), or Agentic systems. Select your preferred embedding providers and LLMs like GPT-4o or Claude.</p>
              </div>
              
              <div className="glass-card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
                <div style={{ width: '60px', height: '60px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem auto', color: 'var(--color-success)', fontSize: '1.5rem', fontWeight: 'bold' }}>3</div>
                <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', fontFamily: 'var(--font-display)' }}>Deploy & Scale</h3>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>Test the results in our interactive playground, then generate an API key to securely integrate the advanced RAG endpoints directly into your production application.</p>
              </div>

            </div>
          </div>
        </section>

        {/* Who we are Section */}
        <section style={{ padding: '6rem 5%' }}>
          <div className="glass-card" style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center', padding: '4rem 3rem', border: '1px solid rgba(168, 85, 247, 0.3)', boxShadow: '0 0 50px -10px rgba(168, 85, 247, 0.2)' }}>
            <h2 style={{ fontSize: '2.5rem', fontFamily: 'var(--font-display)', marginBottom: '1.5rem' }}>Who Are We?</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', lineHeight: 1.8, marginBottom: '2rem' }}>
              We are a team of passionate AI engineers and systems architects dedicated to demystifying complex AI pipelines. 
              We realized that while prototyping a simple Retrieval Augmented Generation app is easy, building reliable, highly-available, and multi-tenant RAG systems at scale is exceptionally hard.
            </p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', lineHeight: 1.8 }}>
              RAGaaS was built to bridge that gap. We handle the heavy lifting of maintaining vector databases, orchestrating embedding pipelines, and caching LLM routing, so you can focus entirely on building incredible product experiences for your users.
            </p>
          </div>
        </section>
        
        {/* Footer */}
        <footer style={{ padding: '2rem 5%', textAlign: 'center', color: 'var(--text-muted)', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <p>© {new Date().getFullYear()} RAGaaS Platform. Designed for builders.</p>
        </footer>
        
      </div>
    </div>
  );
};

export default Landing;
