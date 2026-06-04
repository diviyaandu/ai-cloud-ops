variable "subscription_id" {}
variable "tenant_id" {}
variable "client_id" {}
variable "client_secret" {}
variable "resource_group_name" { default = "rg-finops-prod" }
variable "location"            { default = "eastus" }

variable "default_tags" {
  type = map(string)
  default = {
    Project     = "ai-cloud-ops"
    Environment = "prod"
    Owner       = "platform-team"
    Application = "cloud-ops-dashboard"
  }
}