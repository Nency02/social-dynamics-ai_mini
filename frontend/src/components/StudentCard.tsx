import { motion } from "motion/react";
import { User } from "lucide-react";

interface StudentCardProps {
  studentId: string;
  participation: number;
  role: "Active" | "Moderate" | "Passive";
  index: number;
}

const roleConfig = {
  Active: {
    color: "#00d2d3",
    bgColor: "rgba(0, 210, 211, 0.1)",
    gradient: "from-[#00d2d3] to-[#00b8b9]"
  },
  Moderate: {
    color: "#feca57",
    bgColor: "rgba(254, 202, 87, 0.1)",
    gradient: "from-[#feca57] to-[#feb43f]"
  },
  Passive: {
    color: "#ff9ff3",
    bgColor: "rgba(255, 159, 243, 0.1)",
    gradient: "from-[#ff9ff3] to-[#ff7ee6]"
  }
};

export function StudentCard({ studentId, participation, role, index }: StudentCardProps) {
  const config = roleConfig[role];

  return (
    <motion.div
      className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      whileHover={{ y: -2, scale: 1.02 }}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className="p-2.5 rounded-lg"
            style={{ backgroundColor: config.bgColor }}
          >
            <User className="w-5 h-5" style={{ color: config.color }} />
          </div>
          <div>
            <h4 className="text-gray-800">{studentId}</h4>
          </div>
        </div>

        <div
          className="px-3 py-1 rounded-full text-xs"
          style={{
            backgroundColor: config.bgColor,
            color: config.color
          }}
        >
          {role}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Participation</span>
          <motion.span
            key={participation}
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            className="text-sm text-gray-800"
          >
            {participation}%
          </motion.span>
        </div>

        <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            className={`absolute left-0 top-0 h-full bg-gradient-to-r ${config.gradient} rounded-full`}
            initial={{ width: 0 }}
            animate={{ width: `${participation}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>
      </div>
    </motion.div>
  );
}
