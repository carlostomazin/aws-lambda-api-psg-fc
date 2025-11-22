# IAM Role
resource "aws_iam_role" "lambda_exec" {
  name               = "aws-lambda-api-psg-fc-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Function
resource "aws_lambda_function" "this" {
  function_name    = "aws-lambda-api-psg-fc"
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.13"
  handler          = "main.handler"
  filename         = "../dist/function.zip"
  source_code_hash = filebase64sha256("../dist/function.zip")

  architectures = ["arm64"]

  memory_size = 256
  timeout     = 30

  environment {
    variables = {
      "AWS_LAMBDA_EXEC_WRAPPER": "/opt/bootstrap"
      "PORT": 8000
    }
  }

  layers = [
    "arn:aws:lambda:${data.aws_region.current.name}:753240598075:layer:LambdaAdapterLayerArm64:25"
  ]
}

# Function URL
resource "aws_lambda_function_url" "example" {
  function_name      = aws_lambda_function.this.function_name
  authorization_type = "NONE"
}

# Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/aws-lambda-api-psg-fc"
  retention_in_days = 14
}
