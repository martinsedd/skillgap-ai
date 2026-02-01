data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "portfolio" {
  bucket = "portofolio-bucket-${data.aws_caller_identity.current.account_id}"
}
