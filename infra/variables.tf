variable "artifact_path" {
  description = "Path to the built Lambda zip"
  type        = string
  default     = "../dist/function.zip"
}

variable "function_url_auth_type" {
  description = "Authorization type for Lambda Function URL (NONE or AWS_IAM)"
  type        = string
  default     = "NONE"
}

