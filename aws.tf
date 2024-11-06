# This project runs a simple ECS Function periodically.
# The ECS is triggered by a CloudWatch Event Rule.
# Secrets are stored in AWS Secrets Manager.
# The logs are stored in CloudWatch Logs.
# Define an ECS Cluster
resource "aws_ecs_cluster" "trd_cluster" {
  name = "trd_cluster"
}

resource "aws_secretsmanager_secret" "trd_secret" {
  name        = "trd_scraper_secret"
  description = "This secret is used by the TRD scraper task"
}

resource "aws_secretsmanager_secret_version" "trd_secret_version" {
  secret_id = aws_secretsmanager_secret.trd_secret.id
  secret_string = jsonencode({
    REDCAP_SECRET       = var.redcap_secret,
    TRUE_COLOURS_SECRET = var.true_colours_secret,
    MAILGUN_SECRET      = var.mailgun_secret
  })
}


# Create IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecs_task_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Attach policies to allow ECS tasks to use AWS services
resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Create a custom IAM policy to allow Secrets Manager read-only access
resource "aws_iam_policy" "ecs_secrets_read_policy" {
  name        = "ecs_secrets_read_policy"
  description = "Policy to allow ECS task read-only access to Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.trd_secret.arn
      }
    ]
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "trd_task" {
  family                   = "trd_scraper_task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = "512"
  cpu                      = "256"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "trd_scraper"
      image     = "<your-ecr-repo-url>/trd_scraper:latest"
      memory    = 512
      cpu       = 256
      essential = true
      environment = [
        {
          name  = "GIT_STRING"
          value = "https://github.com/your-org/trd-cli.git"
        }
      ]
      secrets = [
        {
          name      = "REDCAP_SECRET"
          valueFrom = aws_secretsmanager_secret.trd_secret.arn
        },
        {
          name      = "TRUE_COLOURS_SECRET"
          valueFrom = aws_secretsmanager_secret.trd_secret.arn
        },
        {
          name      = "MAILGUN_SECRET"
          valueFrom = aws_secretsmanager_secret.trd_secret.arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/trd_scraper"
          "awslogs-region"        = "eu-west-2"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}


# Run ECS Task periodically using CloudWatch Events
resource "aws_cloudwatch_event_rule" "ecs_schedule_rule" {
  name                = "trd_scraper_schedule_rule"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "ecs_target" {
  rule     = aws_cloudwatch_event_rule.ecs_schedule_rule.name
  arn      = aws_ecs_cluster.trd_cluster.arn
  role_arn = aws_iam_role.ecs_task_execution_role.arn
  ecs_target {
    task_definition_arn = aws_ecs_task_definition.trd_task.arn
    launch_type         = "FARGATE"
    network_configuration {
      subnets          = ["subnet-xxxxxx"] # Replace with your subnet IDs
      security_groups  = ["sg-xxxxxx"]     # Replace with your security group IDs
      assign_public_ip = true
    }
  }
}
