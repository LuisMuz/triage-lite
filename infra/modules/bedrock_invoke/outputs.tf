output "policy_json" {
  description = "Policy document allowing bedrock:InvokeModel through the given global inference profiles only."
  value       = data.aws_iam_policy_document.invoke.json
}
