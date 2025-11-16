/**
 * Dialog component (shadcn/ui compatible)
 */
import * as React from 'react';
import { cn } from '@/lib/utils';

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={() => onOpenChange(false)}
      />
      {children}
    </div>
  );
}

interface DialogContentProps {
  className?: string;
  children: React.ReactNode;
}

export function DialogContent({ className, children }: DialogContentProps) {
  return (
    <div
      className={cn(
        'relative z-50 w-full max-w-lg rounded-lg border bg-background p-6 shadow-lg',
        className
      )}
    >
      {children}
    </div>
  );
}

interface DialogHeaderProps {
  className?: string;
  children: React.ReactNode;
}

export function DialogHeader({ className, children }: DialogHeaderProps) {
  return <div className={cn('flex flex-col space-y-1.5 text-center sm:text-left', className)}>{children}</div>;
}

interface DialogFooterProps {
  className?: string;
  children: React.ReactNode;
}

export function DialogFooter({ className, children }: DialogFooterProps) {
  return (
    <div
      className={cn('flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2', className)}
    >
      {children}
    </div>
  );
}

interface DialogTitleProps {
  className?: string;
  children: React.ReactNode;
}

export function DialogTitle({ className, children }: DialogTitleProps) {
  return <h2 className={cn('text-lg font-semibold leading-none tracking-tight', className)}>{children}</h2>;
}

interface DialogDescriptionProps {
  className?: string;
  children: React.ReactNode;
}

export function DialogDescription({ className, children }: DialogDescriptionProps) {
  return <p className={cn('text-sm text-muted-foreground', className)}>{children}</p>;
}
