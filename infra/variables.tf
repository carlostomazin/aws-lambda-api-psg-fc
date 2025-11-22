variable "environment" {
  description = "Environment variables for Lambda"
  type        = map(string)
  default     = {}
}
