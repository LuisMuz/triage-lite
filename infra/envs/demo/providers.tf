provider "aws" {
  region = var.region

  default_tags {
    tags = {
      project = "triagelite"
      env     = var.env
      owner   = var.owner
    }
  }
}
