terraform {
  backend "s3" {
    bucket = "tgam-personalize-terraform-state-bucket-dev"
    key    = "tgam-personalize"
    region = "us-east-1"
  }
}