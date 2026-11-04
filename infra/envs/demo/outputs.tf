output "data_bucket_name" {
  description = "Bucket that receives CSV uploads and holds run output."
  value       = module.storage.bucket_name
}

output "table_name" {
  description = "DynamoDB table with batches, incidents and clusters."
  value       = module.storage.table_name
}
