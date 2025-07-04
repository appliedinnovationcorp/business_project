# AI Platform - MVP

A comprehensive AI consulting and automation platform for SMBs and enterprises.

## Architecture Overview

- **Backend**: FastAPI with PostgreSQL database
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Infrastructure**: AWS (VPC, RDS, S3, Lambda, AI services)
- **Authentication**: JWT-based authentication
- **AI Services**: AWS Textract, Comprehend, Rekognition

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- AWS CLI configured
- PostgreSQL (for local development)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp ../.env.example .env
# Edit .env with your AWS credentials and database settings
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the backend server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

4. Start the development server:
```bash
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## AWS Infrastructure

The infrastructure is managed with Terraform and includes:

- **VPC**: Custom VPC with public/private subnets
- **RDS**: PostgreSQL database in private subnets
- **S3**: Buckets for data, models, static assets, and backups
- **Security Groups**: Properly configured for web and database access
- **Secrets Manager**: Secure database credential storage

### Deploy Infrastructure

```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

## Features

### MVP Features (Current)
- User authentication and registration
- Project management
- Basic workflow creation
- AWS AI service integration (Textract, Comprehend, Rekognition)
- Document analysis and processing
- Sentiment analysis
- Image analysis

### Planned Features
- Advanced workflow builder with drag-and-drop interface
- AI model marketplace
- Real-time collaboration
- Advanced analytics and reporting
- Industry-specific templates
- Mobile application

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login

### Projects
- `GET /projects` - List user projects
- `POST /projects` - Create new project
- `GET /projects/{id}` - Get project details

### Workflows
- `GET /projects/{id}/workflows` - List project workflows
- `POST /projects/{id}/workflows` - Create new workflow
- `POST /workflows/{id}/execute` - Execute workflow

### Health
- `GET /health` - System health check
- `GET /` - API status

## Development Guidelines

### Code Style
- Backend: Follow PEP 8 for Python code
- Frontend: Use ESLint and Prettier for TypeScript/React
- Use meaningful variable and function names
- Include docstrings and comments for complex logic

### Testing
- Backend: Use pytest for unit and integration tests
- Frontend: Use Jest and React Testing Library
- Maintain >80% code coverage

### Security
- Never commit secrets or API keys
- Use environment variables for configuration
- Implement proper input validation
- Follow AWS security best practices

## Deployment

### Production Deployment
1. Build and deploy infrastructure with Terraform
2. Deploy backend to AWS Lambda or ECS
3. Deploy frontend to AWS Amplify or S3/CloudFront
4. Configure CI/CD pipeline with GitHub Actions

### Environment Variables
Required environment variables are documented in `.env.example`

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review the troubleshooting guide
3. Contact the development team

## License

Proprietary - All rights reserved
