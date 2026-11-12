output "api_url" {
  description = "Base URL of the read API."
  value       = aws_apigatewayv2_stage.default.invoke_url
}
