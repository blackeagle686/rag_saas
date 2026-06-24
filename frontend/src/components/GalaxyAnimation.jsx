import React from 'react';
import './GalaxyAnimation.css';

const GalaxyAnimation = () => {
  return (
    <div className="galaxy-container">
      {/* Central Core & Light Beam */}
      <div className="galaxy-beam"></div>
      <div className="galaxy-core"></div>
      
      {/* Orbiting Rings */}
      <div className="galaxy-ring ring-1"></div>
      <div className="galaxy-ring ring-2"></div>
      <div className="galaxy-ring ring-3"></div>
      
      {/* Dynamic Stars scattered around the galaxy plane */}
      <div className="stars-container">
        {[...Array(70)].map((_, i) => {
          const angle = Math.random() * Math.PI * 2;
          // Distribute stars between radius 90px and 350px
          const radius = 90 + Math.random() * 260;
          const x = Math.cos(angle) * radius;
          const y = Math.sin(angle) * radius;
          // Increase size to compensate for no box-shadow
          const size = Math.random() * 4 + 2;
          
          return (
            <div 
              key={i} 
              className="star" 
              style={{
                left: `calc(50% + ${x}px)`,
                top: `calc(50% + ${y}px)`,
                width: `${size}px`,
                height: `${size}px`,
                animationDelay: `${Math.random() * 5}s`
              }}
            ></div>
          );
        })}
      </div>
    </div>
  );
};

export default GalaxyAnimation;
