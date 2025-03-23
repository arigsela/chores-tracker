# Load Docker Compose config
docker_compose('docker-compose.yml')

# Forward port 8000 (API)
k8s_resource('api', port_forwards='8000:8000')

# Define resources
k8s_resource(
    'api',
    resource_deps=[],
    labels=['backend'],
)

# Set up a live update for the backend
docker_build(
    'chores-tracker-api',
    '.',
    dockerfile='Dockerfile',
    live_update=[
        sync('./backend', '/app/backend'),
        run('pip install -r /app/requirements.txt', trigger='./backend/requirements.txt'),
    ],
)