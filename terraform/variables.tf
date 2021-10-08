#dont use default workspace
resource "null_resource" "is_workspace_valid" {
  triggers = contains(["default"], terraform.workspace) ? file("Workspace name is not correct") : {}

  lifecycle {
    ignore_changes = [triggers]
  }
}

variable "Environment" {
  type    = string
  default = "dev"
}

variable "CostAllocationProduct" {
  type    = string
  default = "amazon_personalize"
}

variable "ResoucesPrefix" {
  type    = string
  default = "tgam-personalize-dev"
}


variable "TrackingId" {
  type    = string
  default = "f19a3e78-4820-4634-ae77-3c9bde0f0b9a"
}


variable "KinesisEventStream" {
  type    = string
  default = "sophi3-transformed-event-stream"
}

variable "KinesisContentStream" {
  type    = string
  default = "sophi3-unified-content-stream"
}

variable "CampainArn" {
  type    = string
  default = "arn:aws:personalize:us-east-1:727304503525:campaign/personalize-poc6-userpersonalization"
}

variable "DataSetArn" {
  type    = string
  default = "arn:aws:personalize:us-east-1:727304503525:dataset/personalize-poc6/ITEMS"
}


locals {
  resource_prefix = "${var.ResoucesPrefix}-${terraform.workspace}"
}
