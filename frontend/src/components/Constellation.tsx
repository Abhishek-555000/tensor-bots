import React, { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRunStore } from '../store/useRunStore';
import { RobotAvatar } from './RobotAvatar';
import { AgentId } from '../types';

// Coordinates mapped onto a 1000x620 SVG viewBox
const AGENT_COORDS: Record<AgentId, { x: number; y: number }> = {
  manager: { x: 500, y: 310 },
  researcher: { x: 210, y: 175 },
  planner: { x: 210, y: 445 },
  developer: { x: 790, y: 175 },
  reviewer: { x: 790, y: 445 },
};

// Natural curved bezier paths between agents
const EDGE_PATHS: Record<string, string> = {
  'manager-researcher': 'M 450,290 C 350,260 280,210 230,170',
  'manager-planner': 'M 450,330 C 350,360 280,410 230,450',
  'researcher-developer': 'M 250,140 C 450,70 550,70 750,140',
  'planner-developer': 'M 250,470 C 440,430 620,330 750,180',
  'developer-reviewer': 'M 800,190 C 830,280 830,340 800,430',
  'reviewer-developer': 'M 770,430 C 740,340 740,280 770,190',
  'reviewer-manager': 'M 750,460 C 650,420 580,360 530,330',
  'manager-developer': 'M 530,290 C 620,240 700,190 760,170',
};

function getAgentCoord(id: string): { x: number; y: number } {
  const norm = (id === 'manager_final' ? 'manager' : id) as AgentId;
  return AGENT_COORDS[norm] || { x: 500, y: 310 };
}

function getEdgePath(fromId: string, toId: string): string {
  const key1 = `${fromId}-${toId}`;
  const key2 = `${toId}-${fromId}`;
  if (EDGE_PATHS[key1]) return EDGE_PATHS[key1];
  if (EDGE_PATHS[key2]) return EDGE_PATHS[key2];

  const p1 = getAgentCoord(fromId);
  const p2 = getAgentCoord(toId);
  const midX = (p1.x + p2.x) / 2;
  const midY = (p1.y + p2.y) / 2 - 25;
  return `M ${p1.x},${p1.y} Q ${midX},${midY} ${p2.x},${p2.y}`;
}

export const Constellation: React.FC = () => {
  const { agents, particles, removeParticle, setActiveAgentModal } = useRunStore();
  const [hoveredAgent, setHoveredAgent] = useState<AgentId | null>(null);

  // Automatically remove particles after flight animation
  useEffect(() => {
    if (particles.length > 0) {
      const timers = particles.map((p) =>
        setTimeout(() => {
          removeParticle(p.id);
        }, 900)
      );
      return () => timers.forEach(clearTimeout);
    }
  }, [particles, removeParticle]);

  return (
    <div
      className="constellation-canvas relative mx-auto flex aspect-[1000/620] w-full items-center justify-center select-none"
      style={{ width: 'min(92vw, 137vh)', maxWidth: '100%' }}
    >
      {/* Background SVG Canvas for Orbit, Edges, and Particles */}
      <svg
        viewBox="0 0 1000 620"
        className="absolute inset-0 w-full h-full pointer-events-none overflow-visible"
      >
        <defs>
          {/* Subtle violet radial glow in center */}
          <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#7C3AED" stopOpacity="0.14" />
            <stop offset="60%" stopColor="#7C3AED" stopOpacity="0.04" />
            <stop offset="100%" stopColor="#7C3AED" stopOpacity="0" />
          </radialGradient>

          {/* Glowing particle filter */}
          <filter id="glowFilter" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Ambient center radial glow circle */}
        <circle cx="500" cy="310" r="340" fill="url(#centerGlow)" />

        {/* Faint Dotted Orbit Rings */}
        <ellipse
          cx="500"
          cy="310"
          rx="380"
          ry="230"
          fill="none"
          stroke="rgba(167, 139, 250, 0.14)"
          strokeWidth="1.2"
          strokeDasharray="4,6"
        />
        <ellipse
          cx="500"
          cy="310"
          rx="220"
          ry="130"
          fill="none"
          stroke="rgba(167, 139, 250, 0.08)"
          strokeWidth="1"
          strokeDasharray="2,6"
        />

        {/* Static Connection Edges */}
        {Object.entries(EDGE_PATHS).map(([key, d]) => (
          <path
            key={key}
            d={d}
            fill="none"
            stroke="rgba(167, 139, 250, 0.18)"
            strokeWidth="1.4"
            strokeDasharray="3,5"
          />
        ))}

        {/* Animated Flying Particles with Neon Trail */}
        {particles.map((particle) => {
          const pathD = getEdgePath(particle.from, particle.to);

          return (
            <g key={particle.id} filter="url(#glowFilter)">
              {/* Highlighted edge line while particle travels */}
              <path
                d={pathD}
                fill="none"
                stroke={particle.color || '#A78BFA'}
                strokeWidth="2.5"
                opacity="0.6"
              />

              {/* Traveling Soft Halo */}
              <circle r="14" fill={particle.color || '#A78BFA'} opacity="0.3">
                <animateMotion
                  path={pathD}
                  dur="0.8s"
                  repeatCount="1"
                  fill="freeze"
                />
              </circle>

              {/* Traveling Core Glow Dot */}
              <circle r="5.5" fill="#FFFFFF">
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
                  ? '#818CF8'
                  : agentId === 'researcher'
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
                  className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-60 p-3.5 rounded-xl bg-[#120A24]/95 backdrop-blur-xl border border-primary/30 shadow-[0_10px_30px_rgba(0,0,0,0.8)] z-30 pointer-events-none"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-text font-mono">{agent.name}</span>
                    <span
                      className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full ${
                        agent.state === 'working'
                          ? 'bg-primary-deep/40 text-primary-light border border-primary/40 animate-pulse'
                          : agent.state === 'done'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                          : agent.state === 'waiting'
                          ? 'bg-purple-900/40 text-purple-300 border border-purple-700/40'
                          : 'bg-white/5 text-text-muted border border-white/10'
                      }`}
                    >
                      {agent.state}
                    </span>
                  </div>
                  <p className="text-[11px] text-text-muted font-mono leading-relaxed line-clamp-2">
                    {agent.statusText || 'Standing by'}
                  </p>
                  {agent.files && agent.files.length > 0 && (
                    <div className="mt-2 text-[10px] text-primary-light border-t border-border-subtle/50 pt-1.5 font-mono flex items-center justify-between">
                      <span>Artifacts written:</span>
                      <span className="font-bold text-emerald-300">{agent.files.length} file{agent.files.length > 1 ? 's' : ''}</span>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}

      {/* Floating Particle Label Mid-Flight Display */}
      {particles.map((p) => {
        const fromCoord = getAgentCoord(p.from);
        const toCoord = getAgentCoord(p.to);
        const midX = (fromCoord.x + toCoord.x) / 2;
        const midY = (fromCoord.y + toCoord.y) / 2;

        return (
          <motion.div
            key={`lbl_${p.id}`}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: [0, 1, 1, 0], scale: [0.9, 1, 1, 0.9], y: -10 }}
            transition={{ duration: 0.8 }}
            className="absolute text-[10px] font-mono tracking-wider px-2.5 py-1 rounded-full bg-[#1A0F33]/90 border border-primary/40 text-primary-light backdrop-blur-md z-20 pointer-events-none shadow-xl"
            style={{
              left: `${(midX / 1000) * 100}%`,
              top: `${(midY / 620) * 100}%`,
              transform: 'translate(-50%, -50%)',
            }}
          >
            ⚡ {p.label}
          </motion.div>
        );
      })}
    </div>
  );
};
