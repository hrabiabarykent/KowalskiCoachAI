import React from 'react';
import { View, Dimensions } from 'react-native';
import { Svg, Rect, Line } from 'react-native-svg';

const screenWidth = Dimensions.get("window").width;

export const getZoneColor = (zoneIndex: number): string => {
  const colors = [
    '#99B1B6', // Z0 (fallback)
    '#99B1B6', // Z1 (gray/teal)
    '#7DBB5E', // Z2 (green)
    '#FFCC2F', // Z3 (yellow)
    '#FA932A', // Z4 (orange)
    '#EB5150', // Z5 (red)
    '#A463B1', // Z6 (purple)
    '#675879'  // Z7 (dark purple)
  ];
  return colors[Math.min(Math.max(zoneIndex, 0), 7)];
};

export const parseStepToChartData = (step: any) => {
  let zone = 2;
  let intensity = 0.65;

  if (step.power) {
    if (step.power.units === 'power_zone' && step.power.value) {
      zone = Math.floor(step.power.value);
    } else if (step.power.units === '%ftp') {
      let val = step.power.value;
      if (step.power.start && step.power.end) val = (step.power.start + step.power.end) / 2;
      if (val) {
        intensity = val / 100.0;
        if (val <= 55) zone = 1;
        else if (val <= 75) zone = 2;
        else if (val <= 90) zone = 3;
        else if (val <= 105) zone = 4;
        else if (val <= 120) zone = 5;
        else if (val <= 150) zone = 6;
        else zone = 7;
      }
    }
  } else if (step.hr) {
    if (step.hr.units === 'hr_zone' && step.hr.value) {
      zone = Math.floor(step.hr.value);
    }
  }

  const txt = (step.text || '').toLowerCase();
  if ((!step.power && !step.hr) || step.pace) {
    if (txt.includes('warmup') || txt.includes('cooldown') || txt.includes('recovery') || txt.includes('rest')) {
      zone = 1;
    } else if (txt.includes('active') || txt.includes('hard') || txt.includes('sprint') || txt.includes('interval')) {
      zone = 6;
      if ((step.duration || 0) < 60) zone = 7;
    }
  }

  if (!step.power || step.power.units !== '%ftp') {
    const zoneIntensities = [0, 0.5, 0.65, 0.85, 1.0, 1.15, 1.35, 1.5];
    intensity = zoneIntensities[Math.min(Math.max(zone, 0), 7)];
  }

  return { duration: step.duration || 0, zone, intensity };
};

export const flattenNestedSteps = (stepsArray: any[], reps: number = 1): any[] => {
  let flat: any[] = [];
  for (let r = 0; r < reps; r++) {
    for (const step of stepsArray) {
      if (step.steps && step.steps.length > 0) {
        flat = flat.concat(flattenNestedSteps(step.steps, step.reps || 1));
      } else {
        flat.push(parseStepToChartData(step));
      }
    }
  }
  return flat;
};

interface WorkoutChartProps {
  workoutDoc: any;
}

export const WorkoutChart: React.FC<WorkoutChartProps> = ({ workoutDoc }) => {
  if (!workoutDoc || !workoutDoc.steps || workoutDoc.steps.length === 0) return null;

  const flatSteps = flattenNestedSteps(workoutDoc.steps);
  const totalDuration = flatSteps.reduce((sum, s) => sum + s.duration, 0);
  if (totalDuration <= 0) return null;

  const chartW = screenWidth - 90;
  const chartH = 120;
  const maxIntensity = 1.6; // We scale up to 160% FTP viewbox

  let currentX = 0;

  return (
    <View style={{ marginVertical: 15, alignItems: 'center' }}>
      <Svg width={chartW} height={chartH}>
        {/* Background Guide Line for 100% Threshold */}
        <Line 
          x1="0" 
          y1={chartH * (1 - 1.0 / maxIntensity)} 
          x2={chartW} 
          y2={chartH * (1 - 1.0 / maxIntensity)} 
          stroke="#555" 
          strokeWidth="1" 
          strokeDasharray="4 4" 
        />

        {/* Fill the bottom with a subtle Z2 green to simulate the continuous base */}
        <Rect 
          x="0" 
          y={chartH * (1 - 0.75 / maxIntensity)} 
          width={chartW} 
          height={chartH * (0.75 / maxIntensity)} 
          fill="#7DBB5E" 
          opacity={0.15} 
        />

        {flatSteps.map((step, idx) => {
          const w = (step.duration / totalDuration) * chartW;
          const h = (step.intensity / maxIntensity) * chartH;
          const y = chartH - h;
          const color = getZoneColor(step.zone);

          const rect = (
            <Rect
              key={idx}
              x={currentX}
              y={y}
              width={w}
              height={h}
              fill={color}
              stroke="#111"
              strokeWidth="0.5"
              opacity={0.9}
            />
          );
          currentX += w;
          return rect;
        })}
      </Svg>
    </View>
  );
};

export default WorkoutChart;
