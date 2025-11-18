/**
 * SuccessCheckmark - Animated checkmark for success states
 *
 * Story 39.40: Micro-interactions - Success animations
 */
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useReducedMotion } from '@/hooks/useReducedMotion';

interface SuccessCheckmarkProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function SuccessCheckmark({ className, size = 'md' }: SuccessCheckmarkProps) {
  const prefersReducedMotion = useReducedMotion();

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  return (
    <div
      className={cn(
        'inline-flex items-center justify-center rounded-full bg-green-500 text-white',
        sizeClasses[size],
        !prefersReducedMotion && 'animate-checkmark',
        className
      )}
    >
      <Check className={cn('h-full w-full p-1')} />
    </div>
  );
}
