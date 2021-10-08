terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.61.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      Environment           = var.Environment
      CostAllocationProduct = var.CostAllocationProduct
      ManagedBy             = "terraform"
      TerraformWorkspace    = terraform.workspace
    }
  }
}
