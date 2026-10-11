import React from 'react';
import { motion } from 'framer-motion';
import { AgentId, AgentState } from '../types';

interface RobotAvatarProps {
  id: AgentId;
  name: string;
  role: string;
  state: AgentState;
  statusText?: string;
  waitingOn?: string[];
  onClick?: () => void;
  accentColor?: string;
}

const AGENT_ICONS: Record<AgentId, React.ReactNode> = {
  // Manager: Branch / Network icon
  manager: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="5" r="3" />
      <circle cx="5" cy="19" r="3" />
      <circle cx="19" cy="19" r="3" />
      <path d="M12 8v4m-5 4l3-2m4 0l3 2" />
    </svg>
  ),
  // Researcher: Search lens icon
  researcher: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.35-4.35" />
    </svg>
  ),
  // Planner: Sparkle / Design drafting icon
  planner: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z" />
    </svg>
  ),
  // Developer: Code </ > icon
  developer: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </svg>
  ),
  // Reviewer: Checkmark shield / badge icon
  reviewer: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  ),
};

export const RobotAvatar: React.FC<RobotAvatarProps> = ({
  id,
  name,
  role,
  state,
  statusText,
  waitingOn,
  onClick,
  accentColor = '#A78BFA',
}) => {
  const isWorking = state === 'working';
  const isWaiting = state === 'waiting';
  const isDone = state === 'done';
  const isError = state === 'error';

  return (
    <div
      onClick={onClick}
      className="group relative flex flex-col items-center cursor-pointer select-none"
      style={{ width: 140 }}
    >
      {/* Isometric Diamond Platform Base */}
      <div className="relative w-28 h-16 flex items-center justify-center">
        {/* Diamond SVG */}
        <svg viewBox="0 0 100 50" className="w-full h-full overflow-visible">
          {/* Subtle Glow under platform */}
          {isWorking && (
            <motion.ellipse
              cx="50"
              cy="25"
              rx="42"
              ry="20"
              fill={accentColor}
              opacity={0.35}
              animate={{ opacity: [0.2, 0.45, 0.2] }}
              transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
            />
          )}

          {/* Isometric Diamond Polygon */}
          <polygon
            points="50,2 95,25 50,48 5,25"
            fill="#120A24"
            stroke={
              isError
                ? '#F87171'
                : isWorking
                ? accentColor
                : isDone
                ? '#34D399'
                : isWaiting
                ? '#7C3AED'
                : 'rgba(167, 139, 250, 0.25)'
            }
            strokeWidth={isWorking ? '2' : '1.2'}
            strokeDasharray={isWaiting ? '4,3' : 'none'}
            className="transition-colors duration-300 group-hover:stroke-primary-light"
          />

          {/* Orbiting ring when working */}
          {isWorking && (
            <motion.ellipse
              cx="50"
              cy="25"
              rx="46"
              ry="22"
              fill="none"
              stroke={accentColor}
              strokeWidth="1"
              strokeDasharray="6,4"
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 6, ease: 'linear' }}
              style={{ originX: '50px', originY: '25px' }}
            />
          )}
        </svg>

        {/* Robot Figure Hovering Above Platform */}
        <motion.div
          animate={
            isWorking
              ? { y: [-2, 2, -2] }
              : isDone
              ? { y: 0 }
              : { y: [-1, 1, -1] }
          }
          transition={{ repeat: Infinity, duration: isWorking ? 1.4 : 3, ease: 'easeInOut' }}
          className="absolute -top-7 flex flex-col items-center"
        >
          {/* Antenna */}
          <div className="relative flex flex-col items-center">
            <div
              className="w-2 h-2 rounded-full mb-0.5 transition-colors duration-300"
              style={{
                backgroundColor: isWorking ? accentColor : isDone ? '#34D399' : '#8B84A3',
                boxShadow: isWorking ? `0 0 8px ${accentColor}` : 'none',
              }}
            />
            <div className="w-0.5 h-2 bg-text-muted opacity-60" />
          </div>

          {/* Robot Head (Rounded Square) */}
          <div
            className="relative w-12 h-11 rounded-xl bg-surface border flex flex-col items-center justify-center p-1 transition-all duration-300 shadow-md group-hover:scale-105"
            style={{
              borderColor: isError
                ? '#F87171'
                : isWorking
                ? accentColor
                : isDone
                ? '#34D399'
                : 'rgba(167, 139, 250, 0.3)',
              boxShadow: isWorking
                ? `0 0 16px ${accentColor}40`
                : '0 4px 12px rgba(0,0,0,0.5)',
            }}
          >
            {/* Eyes Scanner Screen */}
            <div className="relative w-8 h-3.5 bg-[#07040F] rounded-md flex items-center justify-around px-1 overflow-hidden border border-border-subtle">
              {isWorking ? (
                // Scanning visor eye animation
                <motion.div
                  className="w-3 h-2 rounded-full"
                  style={{ backgroundColor: accentColor, boxShadow: `0 0 6px ${accentColor}` }}
                  animate={{ x: [-8, 8, -8] }}
                  transition={{ repeat: Infinity, duration: 1.2, ease: 'easeInOut' }}
                />
              ) : isWaiting ? (
                // Half-closed waiting eyes
                <div className="flex gap-1.5">
                  <div className="w-2 h-0.5 bg-text-muted rounded-full" />
                  <div className="w-2 h-0.5 bg-text-muted rounded-full" />
                </div>
              ) : (
                // Steady or blinking eyes
                <motion.div
                  className="flex gap-1.5"
                  animate={{ opacity: [1, 1, 0.1, 1] }}
                  transition={{ repeat: Infinity, duration: 4, times: [0, 0.85, 0.9, 1] }}
                >
                  <div
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ backgroundColor: isDone ? '#34D399' : '#A78BFA' }}
                  />
                  <div
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ backgroundColor: isDone ? '#34D399' : '#A78BFA' }}
                  />
                </motion.div>
              )}
            </div>

            {/* Chest Glyph / Icon */}
            <div
              className="mt-1 transition-colors duration-300"
              style={{ color: isWorking ? accentColor : isDone ? '#34D399' : '#A78BFA' }}
            >
              <div className="scale-75">{AGENT_ICONS[id]}</div>
            </div>

            {/* Check badge on done */}
            {isDone && (
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center text-[10px] text-black font-bold shadow-sm">
                ✓
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Agent Name & Small Caps Role */}
      <div className="mt-2 text-center pointer-events-none">
        <div className="text-xs font-semibold tracking-wide text-text group-hover:text-primary transition-colors">
          {name}
        </div>
        <div className="text-[10px] font-mono uppercase tracking-wider text-text-muted">
          {role}
        </div>

        {/* Live micro-status text (fades in) */}
        {isWorking && statusText && (
          <motion.div
            initial={{ opacity: 0, y: 2 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-[10px] font-mono text-primary-light mt-1 max-w-[130px] truncate"
            title={statusText}
          >
            {statusText}
          </motion.div>
        )}

        {/* Waiting caption */}
        {isWaiting && (
          <div className="text-[10px] font-mono text-text-faint mt-1 max-w-[130px] truncate">
            {waitingOn && waitingOn.length > 0 ? `waiting on ${waitingOn.join(', ')}` : 'waiting...'}
          </div>
        )}
      </div>
    </div>
  );
};
