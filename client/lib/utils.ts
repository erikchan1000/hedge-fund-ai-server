// src/lib/utils.ts
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Merge className strings with Tailwind conflict deduping.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
