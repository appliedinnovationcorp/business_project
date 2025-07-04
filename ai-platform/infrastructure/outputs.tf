# Output values for use in application configuration

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = [aws_subnet.public_1a.id, aws_subnet.public_1b.id]
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = [aws_subnet.private_1a.id, aws_subnet.private_1b.id]
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "database_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "s3_buckets" {
  description = "S3 bucket names"
  value = {
    data    = aws_s3_bucket.data.bucket
    models  = aws_s3_bucket.models.bucket
    static  = aws_s3_bucket.static.bucket
    backups = aws_s3_bucket.backups.bucket
  }
}

output "security_group_ids" {
  description = "Security group IDs"
  value = {
    web      = aws_security_group.web.id
    database = aws_security_group.database.id
  }
}

output "db_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_password.arn
}
