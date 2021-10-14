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
  default = "0ba2fe37-3a88-4c72-bb22-d4984ce586db"
}


variable "KinesisEventStream" {
  type    = string
  default = "sophi3-transformed-event-stream"
}

variable "KinesisContentStream" {
  type    = string
  default = "sophi3-unified-content-stream"
}

variable "FiltersPrefix" {
  type    = string
  default = "full2"
}

variable "CampainArn" {
  type    = string
  default = "arn:aws:personalize:us-east-1:727304503525:campaign/personalize-full2-userpersonalization"
}

variable "DataSetArn" {
  type    = string
  default = "arn:aws:personalize:us-east-1:727304503525:dataset/personalize-full2/ITEMS"
}


locals {
  resource_prefix = "${var.ResoucesPrefix}-${terraform.workspace}"
}
