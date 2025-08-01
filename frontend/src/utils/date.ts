/**
 * Format a date to a human-readable string
 * @param date The date to format
 * @param formatType The format type (default: 'medium')
 * @returns Formatted date string
 */
export function formatDate(date: Date, formatType: "short" | "medium" | "long" = "medium"): string {
  const options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
  };
  
  if (formatType === "medium" || formatType === "long") {
    options.hour = "2-digit";
    options.minute = "2-digit";
  }
  
  if (formatType === "long") {
    options.second = "2-digit";
  }
  
  return new Intl.DateTimeFormat("en-US", options).format(date);
}