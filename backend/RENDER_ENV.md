# Environment Variables for Render Deployment

The following environment variables need to be configured in your Render dashboard:

## Required Environment Variables

### SECRET_KEY
- **Purpose**: Secret key for JWT token signing and verification
- **Value**: Generate a strong random secret (at least 32 characters)
- **Example**: `abcdefghijklmnopqrstuvwxyz0123456789ABCD`
- **Note**: Use a tool like `openssl rand -hex 32` to generate

### DATABASE_URL
- **Purpose**: Connection string for your PostgreSQL database
- **Format**: `postgresql://username:password@host:port/database_name`
- **Example**: `postgresql://user:password@aws-1-ap-southeast-1.db.render.com:5432/taman_kehati_db`

### ASYNC_DATABASE_URL
- **Purpose**: Async connection string for SQLAlchemy
- **Format**: `postgresql+asyncpg://username:password@host:port/database_name`
- **Example**: `postgresql+asyncpg://user:password@aws-1-ap-southeast-1.db.render.com:5432/taman_kehati_db`

## Optional Environment Variables

### ENV
- **Purpose**: Environment indicator
- **Default**: `production`
- **Values**: `development`, `staging`, `production`

### DEBUG
- **Purpose**: Enable/disable debug mode
- **Default**: `False`
- **Values**: `True`, `False`

### CORS_ORIGINS
- **Purpose**: Comma-separated list of allowed origins
- **Example**: `https://example.com,https://subdomain.example.com`

### ACCESS_TOKEN_EXPIRE_MINUTES
- **Purpose**: Token expiration time in minutes
- **Default**: `60`