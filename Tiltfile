# Load Docker Compose config
docker_compose('docker-compose.yml')

# Build the API image
docker_build(
    'chores-tracker-api',
    '.',
    dockerfile='Dockerfile',
    live_update=[
        sync('./backend', '/app/backend'),
        run('pip install -r /app/requirements.txt', trigger='./backend/requirements.txt'),
    ],
)

# Configure Docker Compose resources
dc_resource('api', labels=['backend'])
dc_resource('mysql', labels=['backend', 'db'])
