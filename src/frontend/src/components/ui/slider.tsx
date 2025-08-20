import * as React from "react"
import { cn } from "@/lib/utils"

export interface SliderProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  value?: number[];
  onValueChange?: (value: number[]) => void;
  min?: number;
  max?: number;
  step?: number;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, value, onValueChange, min = 0, max = 100, step = 1, ...props }, ref) => {
    const currentValue = value?.[0] ?? 0;
    
    return (
      <input
        type="range"
        className={cn(
          "w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700",
          className
        )}
        min={min}
        max={max}
        step={step}
        value={currentValue}
        onChange={(e) => onValueChange?.([parseFloat(e.target.value)])}
        ref={ref}
        {...props}
      />
    )
  }
)
Slider.displayName = "Slider"

export { Slider }
