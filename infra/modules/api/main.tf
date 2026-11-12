locals {
  routes = [
    "GET /batches",
    "GET /batches/{id}",
    "GET /batches/{id}/incidents",
    "GET /batches/{id}/report",
  ]
}

resource "aws_apigatewayv2_api" "read" {
  name          = "${var.name_prefix}-api"
  protocol_type = "HTTP"
  description   = "Read-only API over batches, incidents and reports."
}

resource "aws_apigatewayv2_integration" "function" {
  api_id                 = aws_apigatewayv2_api.read.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.function_invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = var.integration_timeout_ms
}

resource "aws_apigatewayv2_route" "read" {
  #checkov:skip=CKV_AWS_309:Read-only over synthetic demo data with stage throttling; Cognito is a stretch goal (TL-34)
  for_each = toset(local.routes)

  api_id    = aws_apigatewayv2_api.read.id
  route_key = each.value
  target    = "integrations/${aws_apigatewayv2_integration.function.id}"
}

resource "aws_cloudwatch_log_group" "access" {
  #checkov:skip=CKV_AWS_158:Access logs hold request metadata only; a customer-managed KMS key adds cost without protecting anything sensitive
  #checkov:skip=CKV_AWS_338:Fourteen days is enough to investigate abuse of a demo API
  name              = "/aws/apigateway/${var.name_prefix}-api"
  retention_in_days = var.log_retention_days
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.read.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = var.throttling_rate_limit
    throttling_burst_limit = var.throttling_burst_limit
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.access.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      requestTime    = "$context.requestTime"
      sourceIp       = "$context.identity.sourceIp"
      routeKey       = "$context.routeKey"
      path           = "$context.path"
      status         = "$context.status"
      latencyMs      = "$context.responseLatency"
      integrationErr = "$context.integrationErrorMessage"
    })
  }
}

resource "aws_lambda_permission" "api" {
  statement_id  = "AllowReadApi"
  action        = "lambda:InvokeFunction"
  function_name = var.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.read.execution_arn}/*/*"
}
