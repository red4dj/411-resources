# Docker
Useful commands for Docker CLI

## List
### List Images
`docker images`
### List Running Containers
`docker ps`
### List All Containers
`docker ps -a`

## Remove
### Remove Image
`docker rmi <image_name>`
### Remove Container
`docker rm <container_name>`
### Remove All Stopped Containers
`docker container prune`

## Build
`docker build -t <image_name>:<version_number> .`

## Run
`docker run --name <container_name> <image_name>:<version_number>`
<br>(`-p <host_port>:<container_port>`)
### Run & Keep Alive & Detach
`docker run -d --name <container_name> <image_name>:<version_number>`
### &nbsp;&nbsp;&nbsp; Attaching & Detaching
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Press `Ctrl + P`, `Ctrl + Q` to detach from the container without stopping it<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Reattach with `docker attach <container_name>`

### Run with Opening CMD
`docker run --name <container_name> <image_name>:<version_number> bash`

## Start
`docker start <container_name>`

## Execute/Open Shell
`docker exec -it my_container sh`<br>
`docker exec -it my_container bash`

## Stop
`docker stop <container_name>`

### Force Stop
`docker stop -f <container_name>`

## Logs
`docker logs <container_name>`

### Follow Logs Live
`docker logs -f <container_name>`

### Last 20 Logs
`docker logs -n 20 <container_name>`