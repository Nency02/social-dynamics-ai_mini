import { motion } from "motion/react";
import { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  gradient: string;
  highlight?: boolean;
}

export function KPICard({ title, value, subtitle, icon: Icon, gradient, highlight }: KPICardProps) {
  return (
    <motion.div
      className={`bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-lg transition-all duration-300 ${
        highlight ? "ring-2 ring-[#00d2d3] shadow-[0_0_20px_rgba(0,210,211,0.3)]" : ""
      }`}
      whileHover={{ y: -4 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>

      <h3 className="text-gray-500 text-sm mb-2">{title}</h3>

      <motion.div
        key={value}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
        className="text-4xl text-gray-800 mb-1"
      >
        {value}
      </motion.div>

      {subtitle && (
        <p className="text-sm text-gray-600">{subtitle}</p>
      )}
    </motion.div>
  );
}
