terraform {
  backend "s3" {
    bucket       = "triage-state-tf"
    key          = "envs/demo/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
