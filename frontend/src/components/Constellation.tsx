import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRunStore } from '../store/useRunStore';
import { RobotAvatar } from './RobotAvatar';
import { AgentId } from '../types';

// Coordinates mapped onto a 1000x640 SVG viewBox
const AGENT_COORDS: Record<AgentId, { x: number; y: number }> = {
  manager: { x: 500, y: 310 },
  researcher: { x: 210, y: 150 },
  planner: { x: 210, y: 470 },
  developer: { x: 790, y: 150 },
  reviewer: { x: 790, y: 470 },
};

// Edge path definitions between agents
const EDGE_PATHS: Record<string, string> = {
  // manager -> researcher
  'manager-researcher': 'M 450,290 C 350,260 280,210 230,170',
  // manager -> planner
  'manager-planner': 'M 450,330 C 350,360 280,410 230,450',
  // researcher -> developer
  'researcher-developer': 'M 250,140 C 450,70 550,70 750,140',
  // planner -> developer
  'planner-developer': 'M 250,470 C 440,430 620,330 750,180',
  // developer -> reviewer
  'developer-reviewer': 'M 800,190 C 830,280 830,340 800,430',
  // reviewer -> developer (revision loop)
  'reviewer-developer': 'M 770,430 C 740,340 740,280 770,190',
  // reviewer -> manager (approval)
  'reviewer-manager': 'M 750,460 C 650,420 580,360 530,330',
};

export const Constellation: React.FC = () => {
  const { agents, particles, removeParticle, setActiveAgentModal } = useRunStore();
  const [hoveredAgent, setHoveredAgent] = useState<AgentId | null>(null);

  // Automatically remove particles after animation completes (~750ms)
  useEffect(() => {
    if (particles.length > 0) {
      const timers = particles.map((p) =>
        setTimeout(() => {
          removeParticle(p.id);
        }, 850)
      );
      return () => timers.forEach(clearTimeout);
    }
  }, [particles, removeParticle]);

  return (
    <div className="relative w-full h-[620px] max-w-5xl mx-auto flex items-center justify-center">
      {/* Background SVG Canvas for Orbit, Edges, and Particles */}
      <svg
        viewBox="0 0 1000 620"
        className="absolute inset-0 w-full h-full pointer-events-none overflow-visible"
      >
        <defs>
          {/* Subtle violet radial glow in center */}
          <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#7C3AED" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#7C3AED" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Center ambient glow circle */}
        <circle cx="500" cy="310" r="320" fill="url(#centerGlow)" />

        {/* Faint Dotted Orbit Ring */}
        <ellipse
          cx="500"
          cy="310"
          rx="380"
          ry="230"
          fill="none"
          stroke="rgba(167, 139, 250, 0.12)"
          strokeWidth="1.2"
          strokeDasharray="4,6"
        />

        {/* Connection Edges */}
        {Object.entries(EDGE_PATHS).map(([key, d]) => (
          <path
            key={key}
            d={d}
            fill="none"
            stroke="rgba(167, 139, 250, 0.18)"
            strokeWidth="1.4"
            strokeDasharray="3,4"
          />
        ))}

        {/* Animated Flying Particles */}
        {particles.map((particle) => {
          const key = `${particle.from}-${particle.to}`;
          const pathD = EDGE_PATHS[key] || EDGE_PATHS[`${particle.to}-${particle.from}`];
          if (!pathD) return null;

          return (
            <g key={particle.id}>
              {/* Traveling Glow Circle */}
              <circle r="5" fill={particle.color || '#A78BFA'}>
                <animateMotion
                  path={pathD}
                  dur="0.8s"
                  repeatCount="1"
                  fill="freeze"
                />
              </circle>
              {/* Traveling Soft Halo */}
              <circle r="12" fill={particle.color || '#A78BFA'} opacity="0.35">
                <animateMotion
                  path={pathD}
                  dur="0.8s"
                  repeatCount="1"
                  fill="freeze"
                />
              </circle>
            </g>
          );
        })}
      </svg>

      {/* Robot Platforms Placed in Constellation */}
      {Object.entries(AGENT_COORDS).map(([id, pos]) => {
        const agentId = id as AgentId;
        const agent = agents[agentId];

        return (
          <div
            key={agentId}
            style={{
              position: 'absolute',
              left: `${(pos.x / 1000) * 100}%`,
              top: `${(pos.y / 620) * 100}%`,
              transform: 'translate(-50%, -50%)',
            }}
            onMouseEnter={() => setHoveredAgent(agentId)}
            onMouseLeave={() => setHoveredAgent(null)}
          >
            <RobotAvatar
              id={agentId}
              name={agent.name}
              role={agent.role}
              state={agent.state}
              statusText={agent.statusText}
              waitingOn={agent.waitingOn}
              accentColor={
                agentId === 'reviewer'
                  ? '#34D399'
                  : agentId === 'developer'
                  ? '#F472B6'
                  : agentId === 'planner'
                  ? '#38BDF8'
                  : '#A78BFA'
              }
              onClick={() => setActiveAgentModal(agentId)}
            />

            {/* Hover Floating Card */}
            <AnimatePresence>
              {hoveredAgent === agentId && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: 8 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: 4 }}
                  transition={{ duration: 0.15 }}
                  className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-56 p-3 rounded-xl bg-surface/95 backdrop-blur-md border border-border-subtle shadow-subtle-panel z-30 pointer-events-none"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-semibold text-text">{agent.name}</span>
                    <span
                      className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded ${
                        agent.state === 'working'
                          ? 'bg-primary-deep/30 text-primary-light'
                          : agent.state === 'done'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : agent.state === 'waiting'
                          ? 'bg-purple-900/40 text-purple-300'
                          : 'bg-white/5 text-text-muted'
                      }`}
                    >
                      {agent.state}
                    </span>
                  </div>
                  <p className="text-[11px] text-text-muted font-mono leading-relaxed line-clamp-2">
                    {agent.statusText || 'Idle'}
                  </p>
                  {agent.files && agent.files.length > 0 && (
                    <div className="mt-2 text-[10px] text-primary-light border-t border-border-subtle/50 pt-1">
                      {agent.files.length} file{agent.files.length > 1 ? 's' : ''} written
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}

      {/* Floating Particle Label Mid-Flight Display */}
      {particles.map((p) => (
        <motion.div
          key={`lbl_${p.id}`}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: [0, 1, 0.9, 0], scale: 1, y: -8 }}
          transition={{ duration: 0.8 }}
          className="absolute text-[10px] font-mono tracking-wider px-2 py-0.5 rounded-full bg-surface-elevated/90 border border-primary/30 text-primary-light backdrop-blur-sm z-20 pointer-events-none shadow-md"
          style={{
            left: `${((AGENT_COORDS[p.from].x + AGENT_COORDS[p.to].x) / 2 / 1000) * 100}%`,
            top: `${((AGENT_COORDS[p.from].y + AGENT_COORDS[p.to].y) / 2 / 620) * 100}%`,
            transform: 'translate(-50%, -50%)',
          }}
        >
          {p.label}
        </motion.div>
      ))}
    </div>
  );
};
