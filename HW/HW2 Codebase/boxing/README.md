# Boxing
HW2 in BU's CS411 Software Engineering course.

Authored by Davin Martin & Minjie (Zoe) Zuo

# Running the Boxing App with Docker

## Build the Docker Image
`docker build -t boxing-app .`

## Run the Container
```
docker run -d 
  --name boxing-container 
  -v "${PWD}/data:/app/data"  
  -p 5000:5000 
  boxing-app
```

# Running Unit Tests

## Build the Docker Image
`docker build -t boxing-app-tests -f ./tests_dockerfile .`

## Run the Container
```
docker run -d 
  --name boxing-tests-container
  boxing-app-tests
```

# Access The Boxing App
http://127.0.0.1:5000/api/health

## Verify
```
{
  "message": "Service is running",
  "status": "success"
}
```

## Useful Commands
| Action                  | Command                               |
|-------------------------|---------------------------------------|
| List running containers | `docker ps`                           |
| View logs               | `docker logs boxing-container`        |
| Open shell in container | `docker exec -it boxing-container sh` |
| Stop the container      | `docker stop boxing-container`        |
| Remove the container    | `docker rm boxing-container`          |


## Boxing module features
- Add, delete, and get boxers
- Enter two boxers into the ring
- Simulate a fight and determine a winner between two boxers
- Track wins, losses, and leaderboard
