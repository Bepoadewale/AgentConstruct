variable "name" { type = string }
variable "subnet_ids" { type = list(string) }
variable "vpc_id" { type = string }
variable "tags" { type = map(string) }

resource "aws_security_group" "database" {
  name        = "${var.name}-database"
  description = "No public database access; application ingress is added by a reviewed runtime change."
  vpc_id      = var.vpc_id
  tags        = var.tags
}
resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-database"
  subnet_ids = var.subnet_ids
  tags       = var.tags
}
resource "aws_db_instance" "this" {
  identifier                  = var.name
  engine                      = "postgres"
  engine_version              = "16"
  instance_class              = "db.t4g.micro"
  allocated_storage           = 20
  db_name                     = "agentconstruct"
  username                    = "agentconstruct"
  manage_master_user_password = true
  publicly_accessible         = false
  skip_final_snapshot         = false
  deletion_protection         = true
  db_subnet_group_name        = aws_db_subnet_group.this.name
  vpc_security_group_ids      = [aws_security_group.database.id]
  storage_encrypted           = true
  backup_retention_period     = 7
  tags                        = var.tags
}
output "endpoint" { value = aws_db_instance.this.address }
output "master_secret_arn" { value = aws_db_instance.this.master_user_secret[0].secret_arn }
