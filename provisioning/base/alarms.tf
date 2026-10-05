data "aws_sns_topic" "rc_alarms" {
  name = "research-catalog-team-alarms-${var.environment}"
}

resource "aws_cloudwatch_log_metric_filter" "log_error" {
  log_group_name = "/aws/lambda/LocationsService-${var.environment}"
  name           = "LocationsServiceLogError-${var.environment}"
  pattern        = "\"ERROR\""
  region         = "us-east-1"

  metric_transformation {
    name      = "LocationsServiceLogError-${var.environment}"
    namespace = "LogMetrics"
    unit      = "None"
    value     = "1"
  }
}


resource "aws_cloudwatch_metric_alarm" "log_error_alarm" {
  alarm_name        = "LocationsServiceLogErrorAlarm-${var.environment}"
  alarm_description = "Triggered when there's 1 or more error log(s) to LocationsService within 5 minutes."
  namespace         = "LogMetrics"
  metric_name       = "LocationsServiceLogError-${var.environment}"

  statistic = "Sum"

  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"

  datapoints_to_alarm = 1

  treat_missing_data = "notBreaching"

  alarm_actions = [data.aws_sns_topic.rc_alarms.arn]
}

resource "aws_cloudwatch_metric_alarm" "lambda_error_alarm" {
  alarm_name          = "LocationsServiceLambdaErrorAlarm-${var.environment}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Lambda function LocationsService-${var.environment} has invocation errors"
  alarm_actions       = [data.aws_sns_topic.rc_alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = "LocationsService-${var.environment}"
  }

}
