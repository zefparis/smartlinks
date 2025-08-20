import * as React from "react"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

const Sheet = ({ children, open, onOpenChange }: {
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}) => {
  return <div>{children}</div>
}

const SheetTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: boolean }
>(({ className, children, asChild, ...props }, ref) => {
  if (asChild) {
    return <>{children}</>
  }
  return (
    <button
      className={cn("", className)}
      ref={ref}
      {...props}
    >
      {children}
    </button>
  )
})
SheetTrigger.displayName = "SheetTrigger"

const SheetContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { className?: string }
>(({ className, children, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "fixed inset-y-0 right-0 z-50 h-full w-3/4 border-l bg-background p-6 shadow-lg transition ease-in-out sm:max-w-sm",
      className
    )}
    {...props}
  >
    {children}
  </div>
))
SheetContent.displayName = "SheetContent"

const SheetHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col space-y-2 text-center sm:text-left",
      className
    )}
    {...props}
  />
)
SheetHeader.displayName = "SheetHeader"

const SheetTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h2
    ref={ref}
    className={cn("text-lg font-semibold text-foreground", className)}
    {...props}
  />
))
SheetTitle.displayName = "SheetTitle"

const SheetDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
SheetDescription.displayName = "SheetDescription"

export {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
}
