import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "primary" | "success" | "warning" | "danger" | "purple" | "outline";
  size?: "sm" | "md";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "default",
  size = "md",
  children,
  ...props
}) => {
  const baseStyles = "inline-flex items-center font-medium rounded-full select-none";

  const variantStyles = {
    default: "bg-muted text-muted-foreground border border-border/80",
    primary: "bg-primary/10 text-primary border border-primary/20",
    success:
      "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20",
    danger: "bg-red-500/10 text-red-700 dark:text-red-300 border border-red-500/20",
    purple: "bg-purple-500/10 text-purple-700 dark:text-purple-300 border border-purple-500/20",
    outline: "bg-transparent text-foreground border border-border",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[10px]",
    md: "px-2.5 py-0.5 text-xs",
  };

  return (
    <span className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)} {...props}>
      {children}
    </span>
  );
};
