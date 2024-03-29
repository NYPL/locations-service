provider "aws" {
  region     = "us-east-1"
}

variable "environment" {
  type = string
  default = "qa"
  description = "The name of the environment (qa, production). This controls the name of lambda and the env vars loaded."

  validation {
    condition     = contains(["qa", "production"], var.environment)
    error_message = "The environment must be 'qa' or 'production'."
  }
}

# Upload the zipped app to S3:
resource "aws_s3_object" "uploaded_zip" {
  bucket = "nypl-travis-builds-${var.environment}"
  key    = "location-services-${var.environment}-dist.zip"
  acl    = "private"
  source = "../../build/build.zip"
  etag = filemd5("../../build/build.zip")
}

# Create the lambda:
resource "aws_lambda_function" "lambda_instance" {
  description   = "Serves endpoints relating to locations services"
  function_name = "LocationsService-${var.environment}"
  handler       = "main.handler"
  memory_size   = 128
  role          = "arn:aws:iam::946183545209:role/lambda-full-access"
  runtime       = "python3.10"
  timeout       = 60

  # Location of the zipped code in S3:
  s3_bucket     = aws_s3_object.uploaded_zip.bucket
  s3_key        = aws_s3_object.uploaded_zip.key

  # Trigger pulling code from S3 when the zip has changed:
  source_code_hash = filebase64sha256("../../build/build.zip")


  # Load ENV vars from ./config/{environment}.env
  environment {
    variables = {
      ENVIRONMENT = var.environment
      # In order to calculate correct offsets, we need to set the default time zone at deploy time or else AWS will ignore it:
      TZ = "America/New_York"
    }
  }
}
