import { motion } from "motion/react";

interface StatusIndicatorProps {
  connected: boolean;
}

export function StatusIndicator({ connected }: StatusIndicatorProps) {
  return (
    <div className="flex items-center gap-2">
      <motion.div
        className={`w-2.5 h-2.5 rounded-full ${
          connected ? "bg-[#00d2d3]" : "bg-gray-400"
        }`}
        animate={{
          scale: connected ? [1, 1.2, 1] : 1,
          opacity: connected ? [1, 0.7, 1] : 1
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      <span className="text-sm text-gray-600">
        {connected ? "Live" : "Disconnected"}
      </span>
    </div>
  );
}
