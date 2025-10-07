# Deploying Taman Kehati API to Render

This guide will walk you through deploying your FastAPI application to Render, a cloud platform for hosting applications.

## Prerequisites

1. A Render account (sign up at [https://render.com](https://render.com))
2. Your application code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. A PostgreSQL database (you can create one via Render's dashboard)

## Step 1: Prepare Your Repository

Make sure your repository contains the following files:

- `app/main.py` - Your FastAPI application entry point
- `requirements.txt` - Python dependencies
- `Dockerfile` - For containerized deployment (included in this repo)
- `Procfile` - Defines the web service command (included in this repo)

## Step 2: Create a PostgreSQL Database on Render

1. Log in to your Render dashboard
2. Click "New +" and select "PostgreSQL"
3. Enter a name for your database
4. Choose the region closest to your users
5. Select the free plan (or paid plan if needed)
6. Click "Create Database"

After creation, you'll see the connection details. Copy the "External Database URL".

## Step 3: Create Your Web Service

There are two methods to deploy to Render:

### Method 1: Using render.yaml (Recommended)

1. The repository now includes a `render.yaml` file that defines the service configuration
2. In your Render dashboard, click "New +" and select "Import from GitHub/GitLab/Bitbucket"
3. Select your repository containing the Taman Kehati API
4. Render will automatically detect the `render.yaml` file and configure the service based on it

### Method 2: Manual Configuration

1. In your Render dashboard, click "New +" and select "Web Service"
2. Connect your Git repository (GitHub, GitLab, or Bitbucket)
3. Select the repository containing your FastAPI code
4. Choose the branch you want to deploy (usually "main" or "master")
5. Fill in the following details:

   - **Environment**: Docker
   - **Docker image**: Leave blank (Render will use your Dockerfile)
   - **Build Context**: `.` (current directory)
   - **Root Directory**: Leave blank
   - **Start Command**: Don't change this - the Procfile handles it
   - **Environment Variables**: Add the variables listed in RENDER_ENV.md

## Step 4: Configure Environment Variables

Add the following environment variables in the Render dashboard:

- `DATABASE_URL`: Your PostgreSQL database URL from Step 2
- `ASYNC_DATABASE_URL`: Same as DATABASE_URL but with `postgresql+asyncpg://` prefix
- `SECRET_KEY`: Generate a secure secret key (use `openssl rand -hex 32`)
- `ENV`: Set to `production`
- `DEBUG`: Set to `False`

## Step 5: Deploy

1. Click "Create Web Service"
2. Render will start building your application
3. Monitor the build logs in the Render dashboard
4. Once built, your application will be available at the URL provided in the dashboard

## Step 6: Verification

After deployment, verify your application is working:

1. Visit your service URL (provided in the Render dashboard)
2. Check the `/health` endpoint to ensure database connectivity
3. Test API endpoints to ensure everything is functioning

## Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   - Verify your `DATABASE_URL` is correct
   - Ensure the database is running and accessible
   - Check that the database user has proper permissions

2. **Environment Variables Not Set**:
   - Make sure all required environment variables are set in Render dashboard
   - Remember that Render automatically provides the PORT variable

3. **Build Failures**:
   - Check your Dockerfile is correctly formatted
   - Ensure all dependencies in requirements.txt are available
   - Look at build logs in Render dashboard for specific error messages

### Health Check

Your API includes a health check endpoint at `/health` that verifies:
- Database connectivity
- PostGIS availability (if using the original setup)
- Full Text Search (FTS) readiness

## Scaling

Render allows you to scale your service by:
1. Going to your service dashboard
2. Adjusting the instance type under "Scaling & Instances"
3. Increasing the number of instances under "Autoscaling"

## Maintenance

### Updates
To update your application:
1. Push changes to your Git repository
2. Render will automatically detect changes and trigger a new build
3. Monitor the build process in your dashboard

### Logs
View application logs in the "Logs" tab of your Render dashboard to troubleshoot issues.

## Additional Notes

- Render automatically provides the PORT environment variable that your application should use
- Your application uses environment variables for configuration, which works well with Render's environment variable system
- Your Dockerfile is configured to use the PORT environment variable for deployment