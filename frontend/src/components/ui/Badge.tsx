import { type HTMLAttributes } from 'react';
import { cn } from '../../utils/cn';

export type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'purple';

export interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant;
}

function Badge({ className, variant = 'default', children, ...props }: BadgeProps) {
  const variants: Record<BadgeVariant, string> = {
    default: 'bg-surface-2 text-ink-muted border border-hairline',
    success: 'bg-semantic-success/10 text-semantic-success border border-semantic-success/20',
    warning: 'bg-semantic-warning/10 text-semantic-warning border border-semantic-warning/20',
    error: 'bg-semantic-error/10 text-semantic-error border border-semantic-error/20',
    info: 'bg-semantic-info/10 text-semantic-info border border-semantic-info/20',
    purple: 'bg-primary/10 text-primary border border-primary/20',
  };

  return (
    <div
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-colors',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export { Badge };
